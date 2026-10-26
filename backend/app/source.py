import asyncio
import hashlib
import json
import os
import tempfile
import time
from datetime import timedelta
from pathlib import Path
import httpx
from .engine import iso

BASE="https://data.elexon.co.uk/bmrs/api/v1"
CACHE=Path(os.getenv("CACHE_DIR",".cache"))

class SourceError(Exception):
    pass

class Elexon:
    def __init__(self,client):
        self.client=client
        self.gate=asyncio.Semaphore(2)
        self.locks={}
    async def fetch(self,dataset,params):
        key=hashlib.sha256(json.dumps([dataset,params],sort_keys=True).encode()).hexdigest()
        lock=self.locks.setdefault(key,asyncio.Lock())
        async with lock:
            CACHE.mkdir(parents=True,exist_ok=True)
            file=CACHE/(key+".json")
            if file.exists() and time.time()-file.stat().st_mtime<86400:
                try:
                    return json.loads(file.read_text()),{"dataset":dataset,"params":params,"cache":True}
                except (ValueError,OSError):
                    pass
            async with self.gate:
                for attempt in range(4):
                    try:
                        response=await self.client.get(f"{BASE}/datasets/{dataset}/stream",params=params,headers={"Accept":"application/json"})
                        if response.status_code==429 or response.status_code>=500:
                            if attempt<3:
                                retry=response.headers.get("Retry-After","")
                                wait=min(60,float(retry)) if retry.isdigit() else 2**(attempt+1)
                                await asyncio.sleep(wait)
                                continue
                        response.raise_for_status()
                        data=response.json()
                        if isinstance(data,dict):
                            data=data.get("data")
                        if not isinstance(data,list) or any(not isinstance(x,dict) for x in data):
                            raise SourceError("Unexpected Elexon response: expected JSON records")
                        try:
                            with tempfile.NamedTemporaryFile(mode="w",dir=CACHE,delete=False) as f:
                                json.dump(data,f)
                                temp=f.name
                            os.replace(temp,file)
                        except OSError:
                            pass
                        return data,{"dataset":dataset,"params":params,"cache":False}
                    except (httpx.RequestError,httpx.HTTPStatusError,ValueError) as exc:
                        retryable=not isinstance(exc,httpx.HTTPStatusError) or exc.response.status_code in (429,500,502,503,504)
                        if attempt==3 or not retryable:
                            raise SourceError(f"{dataset}: {str(exc)[:240]}") from exc
                        await asyncio.sleep(2**(attempt+1))
            raise SourceError("Elexon request exhausted retries")
    async def day(self,cutoff,start,end,lookback):
        windows=[]
        cursor=cutoff-timedelta(days=lookback)
        # Small publication windows avoid oversized stream requests.
        while cursor<cutoff:
            stop=min(cursor+timedelta(days=1),cutoff)
            windows.append((cursor,stop))
            cursor=stop
        forecast=[]
        provenance=[]
        for lo,hi in windows:
            records,meta=await self.fetch("WINDFOR",{"publishDateTimeFrom":iso(lo),"publishDateTimeTo":iso(hi)})
            forecast.extend(records)
            provenance.append(meta)
        actual,meta=await self.fetch("FUELHH",{"settlementDateFrom":start.date().isoformat(),"settlementDateTo":(end-timedelta(seconds=1)).date().isoformat(),"fuelType":"WIND"})
        provenance.append(meta)
        return forecast,actual,provenance
