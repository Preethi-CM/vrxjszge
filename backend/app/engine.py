from datetime import datetime, timedelta, timezone
from math import sqrt, isfinite
from collections import defaultdict
UTC = timezone.utc

def dt(value):
    result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Timezone required")
    return result.astimezone(UTC)

def iso(value):
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")

def value(raw):
    if raw is None or isinstance(raw, bool):
        raise ValueError("Invalid generation")
    v = float(raw)
    if not isfinite(v) or v < 0:
        raise ValueError("Invalid generation")
    return v

def metrics(rows):
    errors = [r["error"] for r in rows if r["error"] is not None]
    n = len(errors)
    return {"mae":sum(map(abs,errors))/n if n else None,
            "rmse":sqrt(sum(e*e for e in errors)/n) if n else None,
            "bias":sum(errors)/n if n else None,
            "matched":n, "expected":len(rows),
            "coverage":100*n/len(rows) if rows else 0,
            "missingForecast":sum(r["forecast"] is None for r in rows),
            "missingActual":sum(r["actual"] is None for r in rows)}

def evaluate(forecasts, actuals, cutoff, start, end, alignment="exact"):
    cutoff,start,end = map(dt,(cutoff,start,end))
    if alignment not in ("exact","hourly") or end <= start or start < cutoff:
        raise ValueError("Invalid analysis bounds or alignment")
    if any(t.minute or t.second or t.microsecond for t in (start,end)):
        raise ValueError("Delivery bounds must be whole hours")
    diag = {"forecastRecords":len(forecasts),"actualRecords":len(actuals),
            "invalidForecast":0,"invalidActual":0,"postCutoff":0,
            "forecastConflicts":0,"actualConflicts":0,"offGridForecast":0}
    fc,ac = defaultdict(dict),defaultdict(dict)
    for row in forecasts:
        try:
            s,p = dt(row["startTime"]),dt(row["publishTime"])
            if not start <= s < end:
                continue
            if p > cutoff:
                diag["postCutoff"] += 1
                continue
            v = value(row["generation"])
            fc[s].setdefault(p,set()).add(v)
        except (ValueError,TypeError,KeyError,OverflowError):
            diag["invalidForecast"] += 1
    for row in actuals:
        try:
            if row.get("fuelType") != "WIND":
                continue
            s = dt(row["startTime"])
            if not start <= s < end:
                continue
            p = dt(row["publishTime"]) if row.get("publishTime") else datetime.min.replace(tzinfo=UTC)
            v = value(row["generation"])
            ac[s].setdefault(p,set()).add(v)
        except (ValueError,TypeError,KeyError,OverflowError):
            diag["invalidActual"] += 1
    def latest(groups, conflict_key):
        out = {}
        for s,pubs in groups.items():
            p = max(pubs)
            if len(pubs[p]) != 1:
                diag[conflict_key] += 1
                out[s] = (p,None)
            else:
                out[s] = (p,next(iter(pubs[p])))
        return out
    selected, observed = latest(fc,"forecastConflicts"),latest(ac,"actualConflicts")
    step = timedelta(minutes=30 if alignment=="exact" else 60)
    expected_times=[]
    t=start
    while t<end:
        expected_times.append(t)
        t+=step
    diag["offGridForecast"] = sum(s not in set(expected_times) for s in selected)
    rows=[]
    for s in expected_times:
        p,f=selected.get(s,(None,None))
        actual_parts=[observed.get(s,(None,None))]
        if alignment=="hourly":
            actual_parts.append(observed.get(s+timedelta(minutes=30),(None,None)))
        a=sum(x[1] for x in actual_parts)/len(actual_parts) if all(x[1] is not None for x in actual_parts) else None
        err=f-a if f is not None and a is not None else None
        status="matched" if err is not None else "missing_both" if f is None and a is None else "missing_forecast" if f is None else "missing_actual"
        rows.append({"startTime":iso(s),"endTime":iso(s+step),"publishTime":iso(p) if p else None,
                     "forecast":f,"actual":a,"error":err,"status":status,
                     "actualPublications":[iso(x[0]) if x[0] and x[0].year>1 else None for x in actual_parts],
                     "actualComponents":[x[1] for x in actual_parts]})
    pub_times=sorted({r["publishTime"] for r in rows if r["publishTime"]})
    return {"rows":rows,"metrics":metrics(rows),"diagnostics":diag,
            "publicationCount":len(pub_times),"publications":pub_times,
            "sourcePreview":{"forecast":forecasts[:5],"actual":actuals[:5]}}
