"""Run locally: python -m app.verify_live --date 2026-01-10"""
import argparse
import asyncio
import json
from datetime import date,datetime,time,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import httpx
from .source import Elexon
from .engine import evaluate,iso,dt

async def verify(args):
    decision=date.fromisoformat(args.date)
    if decision.year!=2026 or decision.month!=1:
        raise ValueError("Choose a January 2026 decision")
    zone=ZoneInfo("Europe/London")
    cutoff=datetime.combine(decision,time.fromisoformat(args.cutoff),zone)
    start=datetime.combine(decision+timedelta(days=1),time.min,zone)
    end=start+timedelta(days=1)
    async with httpx.AsyncClient(timeout=60,follow_redirects=True) as client:
        forecast,actual,requests=await Elexon(client).day(cutoff,start,end,args.lookback)
    report=evaluate(forecast,actual,iso(cutoff),iso(start),iso(end),args.alignment)
    report.update(decisionDate=str(decision),cutoff=iso(cutoff),requests=requests,
                  note="A live retrieval and mechanical checks, not a confirmation of market or interval semantics.")
    Path("live-validation.json").write_text(json.dumps(report,indent=2))
    for row in report["rows"]:
        if row["publishTime"]:
            assert dt(row["publishTime"])<=dt(iso(cutoff)),"Future forecast selected"
    print(json.dumps(report["metrics"],indent=2))
    print("Saved live-validation.json; inspect raw previews, diagnostics and timestamps manually.")
    if not report["metrics"]["matched"]:
        raise SystemExit("No matched intervals. Validation is NOT complete; inspect source cadence and records.")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--date",default="2026-01-10")
    parser.add_argument("--cutoff",default="10:00")
    parser.add_argument("--lookback",type=int,choices=range(1,8),default=2)
    parser.add_argument("--alignment",choices=["exact","hourly"],default="exact")
    asyncio.run(verify(parser.parse_args()))
