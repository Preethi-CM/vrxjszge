import asyncio
import httpx
import pytest
from app.source import Elexon,SourceError

def test_live_payload_with_mock_transport(tmp_path,monkeypatch):
    import app.source as module
    monkeypatch.setattr(module,"CACHE",tmp_path)
    async def go():
        calls=[]
        def handler(request):
            calls.append(str(request.url))
            return httpx.Response(200,json=[{"startTime":"2026-01-11T00:00:00Z","generation":10}])
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider=Elexon(client)
            a,one=await provider.fetch("WINDFOR",{"publishDateTimeFrom":"2026-01-10T00:00:00Z"})
            b,two=await provider.fetch("WINDFOR",{"publishDateTimeFrom":"2026-01-10T00:00:00Z"})
            assert a==b and len(calls)==1
            assert not one["cache"] and two["cache"]
    asyncio.run(go())

def test_wrapped_payload(tmp_path,monkeypatch):
    import app.source as module
    monkeypatch.setattr(module,"CACHE",tmp_path)
    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r:httpx.Response(200,json={"data":[{"generation":0}]}))) as client:
            rows,_=await Elexon(client).fetch("FUELHH",{})
            assert rows[0]["generation"]==0
    asyncio.run(go())

def test_bad_payload_not_synthetic(tmp_path,monkeypatch):
    import app.source as module
    monkeypatch.setattr(module,"CACHE",tmp_path)
    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r:httpx.Response(200,json={"unexpected":[]}))) as client:
            with pytest.raises(SourceError):await Elexon(client).fetch("WINDFOR",{})
    asyncio.run(go())

def test_400_is_explicit(tmp_path,monkeypatch):
    import app.source as module
    monkeypatch.setattr(module,"CACHE",tmp_path)
    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r:httpx.Response(400,json={"error":"bad query"}))) as client:
            with pytest.raises(SourceError):await Elexon(client).fetch("WINDFOR",{})
    asyncio.run(go())
