# WindLens — historical UK wind forecast intelligence

React + Python/FastAPI assessment implementation for historical UK wind-generation forecast analysis. Uses Elexon API data or cached real responses, with no synthetic fallback.

## Project Links

- Demo video — customer presentation and technical walkthrough:
  https://youtu.be/jh7fBjrg9v8
- Live portal (Vercel):
  https://vrxjszge.vercel.app
- Backend API (Render):
  https://vrxjszge.onrender.com
- API documentation:
  https://vrxjszge.onrender.com/docs
- Repository:
  https://github.com/Preethi-CM/vrxjszge

The demo video is Unlisted and has a total duration of 9 minutes 58 seconds.

The frontend is deployed on Vercel; the backend is deployed separately on Render.

## Validation Status

Read VALIDATION.md for recorded test results and remaining checks.

Initial authoring-tool network failures did not establish whether the deployed application could access historical data. Subsequent deployment checks successfully loaded a single-day exact-alignment scenario and a full-January hourly-alignment scenario.

Downloaded CSV and JSON reports were checked for internal consistency:
- Recalculated MAE, RMSE and bias from exported interval values.
- Compared monthly CSV and JSON forecast, actual and error values.
- Checked selected forecast publication times against decision cutoffs.
- Checked duplicate decision-date/start-time pairs.
- Checked hourly actual values against their exported half-hour components.

These checks do not independently verify every upstream Elexon record, forecast cadence semantics, market assumptions, or every UI feature.

Automated test and production-build outcomes should be recorded only when their actual command results are available.

## Features
- Single decision, custom January range, full-January evaluation.
- Background jobs with day-by-day progress, exact report snapshots and clear source failures.
- MAE/RMSE/bias, expected/matched coverage, daily and aggregate metrics.
- Forecast/actual chart, error chart, biggest misses, searchable/filterable/paginated audit table.
- Interval provenance dialog, raw source previews, request parameters, diagnostics.
- JSON and CSV exports; dark/light appearance; responsive layouts, keyboard focus and reduced-motion support.
- Bounded publication windows, retry/backoff, 24-hour cache of real responses.

## Requirements
Python 3.11+ (3.12 recommended), Node.js 22 LTS and npm. Internet required for installing packages and live Elexon. Windows, macOS or Linux.

## Run locally
### Terminal 1: backend
From the extracted project root:
```sh
cd backend
python -m venv .venv
```
Windows PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
```
If activation is restricted, run `.\.venv\Scripts\python.exe` instead of `python` in subsequent commands. Do not alter system security settings unnecessarily.
macOS/Linux:
```sh
source .venv/bin/activate
```
Then:
```sh
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000 --workers 1
```
Health: http://localhost:8000/api/health
Interactive API: http://localhost:8000/docs

### Terminal 2: frontend
From the extracted project root:
```sh
cd frontend
npm install
npm run dev
```
Open http://localhost:5173. Start with Single day, January 10, 10:00, exact alignment and 2-day lookback. Click Run analysis. Live API access may take time. Use Full January only after validating one day.

### Commands
Backend, with environment active:
```sh
python -m pytest -q
```
Frontend:
```sh
npm run build
npm run preview
```
Preview uses a different origin/port; add that exact origin to ALLOWED_ORIGINS and restart backend if using preview.

## Folder structure
```
backend/app/engine.py      pure selection, matching, conflict and metric logic
backend/app/source.py      Elexon requests, retries and cache
backend/app/main.py        validation, jobs, progress, exports
backend/tests/             engine and mocked integration tests
frontend/src/main.jsx     React views and user flow
frontend/src/style.css    responsive dual-theme UI
```

## API
POST /api/jobs with JSON:
```json
{"start_date":"2026-01-01","end_date":"2026-01-31","cutoff_time":"10:00","alignment":"exact","lookback_days":2}
```
GET /api/jobs/{id}: status and completedDays.
GET /api/jobs/{id}/result: complete/partial report.
GET /api/jobs/{id}/export.csv: full loaded report, not only frontend-filtered rows.
GET /api/health: backend health, NOT proof that Elexon is reachable.

## Data sources
https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream
https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream
API base: https://data.elexon.co.uk/bmrs/api/v1
WINDFOR uses publishDateTimeFrom/To. FUELHH uses settlementDateFrom/To and fuelType=WIND. Do not combine actual settlement filters with publication filters. No API key is configured.

## Explicit assumptions and policies
1. Decision dates are January 1–31, 2026 in Europe/London. Delivery is the NEXT calendar day. January 31 therefore uses February 1 delivery. All joins are normalized to UTC.
2. Default cutoff 10:00 is editable and is NOT an asserted official market gate closure. Confirm the required decision rule with the brief/reviewer.
3. Latest eligible publishTime <= cutoff is selected independently per delivery startTime. Multiple publication snapshots may contribute to one delivery day. This is not a single-snapshot policy.
4. Forecast search is bounded to lookback_days (1–7; default 2). Missing may mean outside window. Use a wider lookback if justified. Full month with wider windows is slower; cache reduces repeated requests.
5. Exact mode builds a 30-minute expected grid, compares identical timestamps and does NOT interpolate. If forecast cadence is hourly or otherwise different, half-hour coverage can legitimately be incomplete.
6. Optional hourly mode is a documented modeling assumption: forecast on the hour represents that hour's average MW. Actual is the mean of both half-hour values; both must exist. Verify source semantics before treating hourly accuracy as authoritative. Off-hour forecasts are counted in diagnostics and not silently shifted.
7. Actual FUELHH values are average MW over half hours. They are not MWh. This project evaluates MW errors, not costs or traded energy.
8. Latest returned actual revision is selected, regardless of decision cutoff; actuals are retrospective targets. Missing actual publication timestamps are allowed but not invented.
9. Same delivery+publication timestamp with identical values is deduplicated. Conflicting latest values are excluded/flagged; no arbitrary maximum-value fallback.
10. Nonfinite, negative, boolean or null generation values are invalid. Numeric zero is valid.
11. MAE = sum(abs(error))/matched; RMSE = sqrt(sum(error^2)/matched); bias = sum(error)/matched. error = forecast − actual. Period metrics are calculated across matched intervals, NOT unweighted daily averages.
12. All requested delivery intervals count toward coverage, including completely failed source days. Metrics can be null. Source failures are explicit and never replaced with fake data.

### Metrics

For matched interval i, error = forecast minus actual.

- MAE: average absolute error.
- RMSE: square root of the average squared error.
- Bias: average signed error; positive means overforecasting, negative means underforecasting.
- Coverage: matched intervals divided by expected intervals, multiplied by 100.

Accuracy metrics are expressed in MW. Coverage is expressed as a percentage. Missing observations are not treated as zero-error observations.

## Using the portal

1. Open the live portal.
2. Choose a single day, date range, or full January.
3. Set the decision cutoff, alignment policy, and publication lookback.
4. Run the analysis. Full-month processing may take several minutes.
5. Read coverage and warnings together with the accuracy metrics.
6. Inspect the forecast-versus-actual chart.
7. Download CSV or JSON for further review.

## Reproduced validation scenarios

The following figures were checked against the supplied exports during deployment validation. They describe specific scenarios, not guaranteed future results.

| Setting / result | Single-day example | Full-January example |
| --- | --- | --- |
| Decision dates | January 10, 2026 | January 1–31, 2026 |
| Cutoff | 10:00 London | 10:00 London |
| Lookback | 2 days | 2 days |
| Alignment | Exact, 30 minutes | Hourly |
| Expected intervals | 48 | 744 |
| Matched intervals | 24 | 744 |
| Coverage | 50% | 100% |
| MAE | 4,948.5 MW | 2,013.0 MW |
| RMSE | 5,020.5 MW | 2,505.9 MW |
| Bias | +4,948.5 MW | +1,729.9 MW |

The single-day export contains 24 `missing_forecast` rows. The monthly export contains 744 matched rows across 31 decision days.

These scenarios use different dates and alignment policies. Their accuracy and coverage must not be interpreted as a controlled before-and-after improvement.
## User flow
1. Define scope/cutoff/alignment/lookback.
2. Run analysis -> see progress -> inspect loaded scenario and coverage.
3. Overview -> forecast vs actual -> daily summary.
4. Accuracy lab -> error chart -> largest misses.
5. Data explorer -> filter/search -> inspect publication/actual provenance.
6. Methodology -> source diagnostics/requests -> export CSV/JSON.
Changing controls does not change an already loaded report until Run analysis is clicked. Day filters affect charts/tables; top metric cards remain full-scenario metrics, as labeled.

## Live validation helper
With the backend environment active, from backend:
```sh
python -m app.verify_live --date 2026-01-10
```
This fetches real records and saves local live-validation.json with previews, requests and metrics. It exits with an error if no intervals match. It checks the cutoff mechanically, but you must still inspect cadence and source semantics manually. This helper has NOT been run against the live API in the authoring environment.

## Live acceptance checks (must execute locally)
- Health check returns ok; backend docs open; frontend has no runtime errors.
- Run January 10 exact mode. Inspect several raw forecast/actual records in Methodology.
- Check forecast cadence, actual half-hour cadence, UTC offsets and source semantics.
- For every selected forecast, verify publishTime <= cutoff. Manually verify one selection and error.
- Examine diagnostics, missing coverage, invalid records and timestamp conflicts.
- If considering hourly mode, justify the hourly interpretation with source documentation; never choose it only to hide missing data.
- Test January 1 and January 31, then run full January.
- Confirm overall metrics from exported matched errors and coverage across all days.
- Stop backend/disconnect network and verify visible errors and no fallback.
- Check mobile, keyboard navigation, dialog close/Escape, exports and themes.
- Run tests and frontend production build. Record actual results in VALIDATION.md.

## Deployment
Backend must be one process/worker because jobs live in memory. Start `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1`. Set service root backend; build `pip install -r requirements.txt`. Dockerfile provided. Optional Docker Compose runs backend only; run frontend with npm separately.
Set backend ALLOWED_ORIGINS to the exact HTTPS frontend origin (comma-separated if several). Set frontend VITE_API_BASE_URL to the backend HTTPS origin, without /api suffix. Build Vite frontend on Vercel with root frontend, build npm run build, output dist. Rebuild after changing frontend environment variables.
The application is deployed with the frontend on Vercel and the backend on Render. Provider availability and pricing are subject to their current terms. Vercel frontend alone does not run the separately hosted Python service. Keep backend awake while analysing; ephemeral restarts lose jobs.

### Deployed environment configuration

Frontend:

```dotenv
VITE_API_BASE_URL=[https://vrxjszge.onrender.com](https://vrxjszge.onrender.com)
```

Backend:

```dotenv
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,[https://vrxjszge-1.onrender.com,[https://vrxjszge.vercel.app](https://vrxjszge.vercel.app)](https://vrxjszge-1.onrender.com,[https://vrxjszge.vercel.app](https://vrxjszge.vercel.app))
```

The older Render frontend origin is retained for compatibility.
The primary portal URL is https://vrxjszge.vercel.app.

## Deliberate limitations
Background job state and reports live in memory, expire after two hours when new jobs arrive and are lost on restart. One analysis runs at a time per server. Use one worker. For production use a durable queue, database, authentication and distributed rate limiting. Cache contains public source records, is ephemeral unless mounted, and does not prove historical source completeness. There is no trading execution, price optimization, new forecasting model, or guaranteed network access. The demonstrated deployment checks establish successful scenario execution and export consistency, not comprehensive source validation or production readiness. This is a time-boxed assessment application, not production trading infrastructure.


## AI Assistance Disclosure

Perplexity AI assisted with project development, documentation, deployment guidance, troubleshooting, and export-consistency analysis.

I performed the deployed portal walkthrough, ran the demonstrated analysis scenarios, downloaded the reports, and recorded the customer and technical demonstration.

The exported results were checked with AI-assisted calculations. These checks establish internal consistency, not independent verification of every upstream record.

Automated test execution, production-build results, and manual code-review work are documented separately in VALIDATION.md where completed.

## Submission Checklist

- [x] Frontend deployed on Vercel.
- [x] Backend deployed on Render.
- [x] Single-day analysis results loaded.
- [x] Full-January hourly analysis results loaded.
- [x] CSV and JSON exports downloaded and checked.
- [x] Unlisted YouTube demo uploaded.
- [x] Video link opened successfully in an Incognito window.



