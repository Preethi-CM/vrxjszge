import asyncio
import csv
import io
import os
import time as clock
from contextlib import asynccontextmanager
from datetime import date,datetime,time,timedelta
from typing import Literal
from uuid import uuid4
from zoneinfo import ZoneInfo
import httpx
from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel,Field,model_validator
from .engine import evaluate,metrics,iso
from .source import Elexon

class Scenario(BaseModel):
    start_date:date=date(2026,1,10)
    end_date:date=date(2026,1,10)
    cutoff_time:str=Field(default="10:00",pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    alignment:Literal["exact","hourly"]="exact"
    lookback_days:int=Field(default=2,ge=1,le=7)
    @model_validator(mode="after")
    def dates(self):
        if not date(2026,1,1)<=self.start_date<=self.end_date<=date(2026,1,31):
            raise ValueError("Decision range must be ordered and inside January 2026")
        return self

jobs={}
tasks=set()

@asynccontextmanager
async def lifespan(app):
    async with httpx.AsyncClient(timeout=httpx.Timeout(60),follow_redirects=True) as client:
        app.state.source=Elexon(client)
        yield
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks,return_exceptions=True)

app=FastAPI(title="WindLens",version="2.0.0",lifespan=lifespan)
app.add_middleware(CORSMiddleware,
    allow_origins=[x.strip().rstrip("/") for x in os.getenv("ALLOWED_ORIGINS","http://localhost:5173,http://127.0.0.1:5173").split(",") if x.strip()],
    allow_methods=["GET","POST"],allow_headers=["*"])

async def run_job(job,scenario,source):
    zone=ZoneInfo("Europe/London")
    days=[]
    errors=[]
    allrows=[]
    cursor=scenario.start_date
    try:
        while cursor<=scenario.end_date:
            job["message"]=f"Fetching and evaluating decision {cursor}"
            cutoff=datetime.combine(cursor,time.fromisoformat(scenario.cutoff_time),zone)
            start=datetime.combine(cursor+timedelta(days=1),time.min,zone)
            end=start+timedelta(days=1)
            try:
                forecasts,actuals,provenance=await source.day(cutoff,start,end,scenario.lookback_days)
                result=evaluate(forecasts,actuals,iso(cutoff),iso(start),iso(end),scenario.alignment)
                for row in result["rows"]:
                    row.update(decisionDate=str(cursor),cutoff=iso(cutoff))
                summary={k:v for k,v in result.items() if k!="rows"}
                summary.update(decisionDate=str(cursor),cutoff=iso(cutoff),deliveryStart=iso(start),deliveryEndExclusive=iso(end),requests=provenance)
                days.append(summary)
                allrows.extend(result["rows"])
            except Exception as exc:
                # Failed source requests remain explicit; their expected intervals count in coverage.
                empty=evaluate([],[],iso(cutoff),iso(start),iso(end),scenario.alignment)
                for row in empty["rows"]:
                    row.update(decisionDate=str(cursor),cutoff=iso(cutoff),status="source_error")
                allrows.extend(empty["rows"])
                errors.append({"decisionDate":str(cursor),"message":str(exc)[:400]})
            job["completedDays"]+=1
            cursor+=timedelta(days=1)
        warnings=["Cutoff is a user-defined scenario assumption, not a verified market gate closure.",
                  "Per-interval latest publication selection can mix forecast publication times.",
                  f"Forecast publication search is bounded to {scenario.lookback_days} day(s); missing records may exist earlier.",
                  "Actuals use the latest returned revisions; metrics are retrospective."]
        if scenario.alignment=="hourly":
            warnings.append("Hourly mode assumes each on-the-hour forecast represents that hour's average MW; actual is the mean of two complete half-hour readings. Verify this interpretation with source semantics before submission.")
        else:
            warnings.append("Exact mode compares coincident timestamps only; if forecast cadence differs, full half-hour coverage is not expected. No interpolation is performed.")
        if errors:
            warnings.append("Some days failed at the source; their expected intervals remain in the coverage denominator.")
        combined=metrics(allrows)
        if combined["coverage"]<100:
            warnings.append("Incomplete coverage: accuracy describes matched pairs, not the entire requested period.")
        job["result"]={"scenario":scenario.model_dump(mode="json"),"metrics":combined,"days":days,"rows":allrows,"errors":errors,"warnings":warnings,"generatedAt":iso(datetime.now(zone)),"source":"Elexon live API (or cached live response)","units":"MW","intervalMinutes":30 if scenario.alignment=="exact" else 60}
        job["status"]="complete" if not errors else "partial" if days else "failed"
        job["message"]="Analysis ready" if days else "All source requests failed; inspect errors and retry"
    except asyncio.CancelledError:
        job["status"]="cancelled"
        raise
    except Exception as exc:
        job["status"]="failed"
        job["message"]=str(exc)[:400]

@app.get("/api/health")
def health():
    return {"status":"ok","source":"Elexon","syntheticFallback":False}

@app.post("/api/jobs",status_code=202)
async def create_job(scenario:Scenario):
    now=clock.time()
    for key in list(jobs):
        if jobs[key]["status"]!="running" and now-jobs[key]["created"]>7200:
            del jobs[key]
    if any(j["status"]=="running" for j in jobs.values()):
        raise HTTPException(429,"An analysis is already running on this server. Wait for it to finish.")
    if len(jobs)>=100:
        oldest=min(jobs,key=lambda k:jobs[k]["created"])
        del jobs[oldest]
    ident=uuid4().hex
    job={"id":ident,"created":now,"status":"running","completedDays":0,"totalDays":(scenario.end_date-scenario.start_date).days+1,"message":"Queued","result":None}
    jobs[ident]=job
    task=asyncio.create_task(run_job(job,scenario,app.state.source))
    tasks.add(task)
    task.add_done_callback(tasks.discard)
    return {"id":ident,"status":"running"}

def find(ident):
    if ident not in jobs:
        raise HTTPException(404,"Analysis not found. Server may have restarted; run it again.")
    return jobs[ident]

@app.get("/api/jobs/{ident}")
def progress(ident:str):
    job=find(ident)
    return {k:v for k,v in job.items() if k not in ("result","created")}

@app.get("/api/jobs/{ident}/result")
def result(ident:str):
    job=find(ident)
    if job["result"] is None:
        raise HTTPException(409,"Result not ready")
    return job["result"]

@app.get("/api/jobs/{ident}/export.csv")
def export(ident:str):
    report=result(ident)
    out=io.StringIO(newline="")
    keys=["decisionDate","cutoff","startTime","endTime","publishTime","forecast","actual","error","status"]
    writer=csv.DictWriter(out,fieldnames=keys,extrasaction="ignore")
    writer.writeheader()
    writer.writerows(report["rows"])
    return Response(out.getvalue(),media_type="text/csv",headers={"Content-Disposition":'attachment; filename="windlens-live-analysis.csv"'})
