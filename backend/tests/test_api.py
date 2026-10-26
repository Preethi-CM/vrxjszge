import asyncio
from datetime import date
import httpx
import pytest
pytest.importorskip("fastapi", reason="Install backend/requirements.txt to run FastAPI integration tests")
from fastapi.testclient import TestClient
from app.main import app,jobs,Scenario,run_job
from app.source import Elexon,SourceError

class Fake:
    async def day(self,cutoff,start,end,lookback):
        return ([{"startTime":start.isoformat(),"publishTime":cutoff.isoformat(),"generation":100}],
                [{"startTime":start.isoformat(),"publishTime":end.isoformat(),"fuelType":"WIND","generation":90}],[])

def test_invalid_scenario():
    with pytest.raises(ValueError):Scenario(start_date=date(2025,12,31))

def test_api_job_and_csv():
    jobs.clear()
    with TestClient(app) as client:
        app.state.source=Fake()
        response=client.post("/api/jobs",json={"start_date":"2026-01-10","end_date":"2026-01-10"})
        assert response.status_code==202
        ident=response.json()["id"]
        import time
        for _ in range(50):
            state=client.get(f"/api/jobs/{ident}").json()
            if state["status"]!="running":break
            time.sleep(.01)
        report=client.get(f"/api/jobs/{ident}/result").json()
        assert report["metrics"]["mae"]==10
        assert report["metrics"]["expected"]==48
        assert client.get(f"/api/jobs/{ident}/export.csv").status_code==200
        assert client.get("/api/jobs/missing").status_code==404

class Broken:
    async def day(self,*args):raise SourceError("upstream unavailable")

def test_failed_day_keeps_denominator():
    job={"completedDays":0}
    asyncio.run(run_job(job,Scenario(),Broken()))
    assert job["status"]=="failed"
    assert job["result"]["metrics"]["expected"]==48
    assert len(job["result"]["errors"])==1

def test_month_boundaries():
    job={"completedDays":0}
    asyncio.run(run_job(job,Scenario(start_date=date(2026,1,1),end_date=date(2026,1,31)),Fake()))
    assert job["result"]["metrics"]["expected"]==31*48
    assert job["result"]["days"][-1]["deliveryStart"].startswith("2026-02-01")

def test_source_payload_and_cache(tmp_path,monkeypatch):
    import app.source as module
    monkeypatch.setattr(module,"CACHE",tmp_path)
    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request:httpx.Response(200,json=[{"generation":10}]))) as client:
            provider=Elexon(client)
            one,meta=await provider.fetch("WINDFOR",{"x":"1"})
            two,meta=await provider.fetch("WINDFOR",{"x":"1"})
            assert one==two and meta["cache"] is True
    asyncio.run(go())
