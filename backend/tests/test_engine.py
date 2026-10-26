import math
import pytest
from app.engine import evaluate,metrics,dt
C="2026-01-10T10:00:00Z"
S="2026-01-11T00:00:00Z"
H="2026-01-11T00:30:00Z"
E="2026-01-11T01:00:00Z"
def f(v,p=C,s=S):
    return {"startTime":s,"publishTime":p,"generation":v}
def a(v,s=S,p="2026-01-12T00:00:00Z"):
    return {**f(v,p,s),"fuelType":"WIND"}
def test_latest_before_cutoff():
    r=evaluate([f(10,"2026-01-10T09:00:00Z"),f(20),f(99,"2026-01-10T11:00:00Z")],[a(18)],C,S,E)
    assert r["rows"][0]["forecast"]==20
    assert r["diagnostics"]["postCutoff"]==1
def test_metrics():
    m=evaluate([f(20),f(10,s=H)],[a(18),a(14,H)],C,S,E)["metrics"]
    assert m["mae"]==3
    assert m["rmse"]==pytest.approx(math.sqrt(10))
    assert m["bias"]==-1
    assert m["coverage"]==100
def test_zero_and_missing():
    r=evaluate([f(0)],[a(0)],C,S,E)
    assert r["rows"][0]["error"]==0
    assert r["rows"][1]["actual"] is None
    assert r["metrics"]["coverage"]==50
def test_empty_metrics():
    assert evaluate([],[],C,S,E)["metrics"]["mae"] is None
def test_timezone():
    assert evaluate([f(20,"2026-01-10T11:00:00+01:00")],[a(18)],C,S,E)["rows"][0]["forecast"]==20
def test_actual_revision():
    r=evaluate([f(20)],[a(4,p="2026-01-11T01:00:00Z"),a(18)],C,S,E)
    assert r["rows"][0]["actual"]==18
def test_conflicts_excluded():
    r=evaluate([f(10),f(20)],[a(18)],C,S,E)
    assert r["rows"][0]["forecast"] is None
    assert r["diagnostics"]["forecastConflicts"]==1
def test_duplicate_same_value_ok():
    assert evaluate([f(20),f(20)],[a(18)],C,S,E)["rows"][0]["forecast"]==20
def test_invalid_records():
    r=evaluate([f(None),f(-1),f(float("inf")),{}],[a(18)],C,S,E)
    assert r["diagnostics"]["invalidForecast"]==4
def test_hourly_mean():
    r=evaluate([f(20)],[a(10),a(30,H)],C,S,E,"hourly")
    assert r["rows"][0]["actual"]==20
    assert r["metrics"]["expected"]==1
def test_hourly_incomplete():
    assert evaluate([f(20)],[a(10)],C,S,E,"hourly")["rows"][0]["actual"] is None
def test_other_fuel_excluded():
    row=a(10);row["fuelType"]="GAS"
    assert evaluate([f(20)],[row],C,S,E)["rows"][0]["actual"] is None
def test_no_naive_timestamps():
    with pytest.raises(ValueError):dt("2026-01-10T10:00:00")
def test_bad_bounds():
    with pytest.raises(ValueError):evaluate([],[],E,S,E)
def test_error_weighted_not_daily_mean():
    rows=[{"error":2,"forecast":2,"actual":0},{"error":-4,"forecast":0,"actual":4},{"error":None,"forecast":None,"actual":5}]
    assert metrics(rows)["mae"]==3
    assert metrics(rows)["expected"]==3
