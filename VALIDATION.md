# Validation record

All checks below were run locally on Windows with Docker Desktop against live Elexon data.
Items marked **Not done** have not been performed.

## Environment
- Python 3.14.2 (local venv); the Docker image uses Python 3.12 (`python:3.12-slim`).
- Node.js 22.18.0.

## Automated checks
- Backend: `python -m pytest -q` in `backend` -> **24 passed** (1 deprecation warning).
- Frontend: `npm run build` -> passed (chunk-size warning only).
- Docker: `docker compose -f docker-compose.full.yml up --build` -> `api` (Uvicorn on :8000) and `web` (nginx) both started; the app opened at http://localhost:5173 with "Backend online" and ran live analyses.

## Single decision: 10 January 2026 (delivery 11 January, cut-off 10:00 Europe/London)
| Alignment | Matched | MAE (MW) | RMSE (MW) | Bias (MW) |
|---|---|---|---|---|
| Exact timestamps, 30-min grid | 24 of 48 (50%) | 4,948.5 | 5,020.5 | +4,948.5 |
| Hourly actual mean | 24 of 24 (100%) | 4,897.1 | 4,966.2 | +4,897.1 |

Exact mode matches only 24 of 48 slots because the forecasts in the data are hourly (values on the hour only), so there is no half-hour forecast to compare with. That is the reason hourly mode is used for the reported results; it was not chosen to hide missing data.

## Full January: decisions 1-31 January 2026
Settings: cut-off 10:00 Europe/London, delivery on the next calendar day, hourly actual mean (explicit assumption), 2-day lookback.

- Dashboard: 744 of 744 hourly comparisons matched; MAE 2,013 MW; RMSE 2,505.9 MW; bias +1,729.9 MW.
- Independent recalculation from the exported CSV: MAE 2,013.0081 MW; RMSE 2,505.9431 MW; bias +1,729.9315 MW. All three agree with the dashboard after rounding.
- CSV checks (local script): January decision dates, 24 hourly rows per day, no duplicate decision/delivery pairs, cut-off eligibility, next-day delivery, finite numbers, error arithmetic.
- From the CSV: every one of the 744 rows uses a publication at or before its cut-off (all published 09:30 UTC; lead time 14.5-37.5 h); the forecast is above the actual in about 84% of intervals; the largest over-forecast is 6,833 MW and the largest under-forecast is 4,128 MW. The cause of the positive bias has not been investigated.

## Manual check against the raw Elexon API
- **FUELHH (`fuelType=WIND`), 2026-01-02:** the two half-hour values of each hour, averaged, equal the app's hourly actual for 00:00, 01:00, 02:00 and 03:00 UTC: 15,366.5; 15,681; 15,875; 16,110.5 MW.
- **WINDFOR, publish window 2026-01-01 09:00-10:00 UTC:** the response contained a single publication run (09:30 UTC, before the 10:00 cut-off). Its values for 2026-01-02 00:00-03:00 UTC (18,699; 18,863; 18,927; 18,979 MW) equal the forecasts in the export.
- First export row: 18,699 - 15,366.5 = 3,332.5, as shown.

## Assumptions still open
- The hourly interpretation (a forecast on the hour represents that hour's average MW, compared with the mean of the two half-hour actuals) is an explicit assumption; the source documentation has not been used to confirm it.
- The 10:00 cut-off is a scenario assumption, not an official gate closure.
- The manual selection check covers one day; the full-month check covers every exported row's publish time against its cut-off, but does not prove that no later eligible publication exists on every day.

## Not done
- Deployment (Heroku backend, Vercel frontend) and the cross-origin browser check.
- Public-access checks in an incognito window (app, repository, video).
- Repository creation, video upload and form submission.
