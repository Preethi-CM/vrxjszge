# WindLens - historical UK wind forecast intelligence

A React + Python (FastAPI) web app for a day-ahead trading desk. It answers two questions with Elexon BMRS data only:
1. What wind forecast was available at the decision cut-off?
2. How accurate was it, in numbers?

Live Elexon data only (FUELHH actuals, WINDFOR forecasts). No synthetic fallback and no invented analytics.

- **Live app:** `<ADD VERCEL URL>`
- **Backend API (Heroku):** `<ADD HEROKU URL>` (health check: `/api/health`)
- **Demo video (unlisted):** `<ADD YOUTUBE URL>`

## Results at a glance (January 2026 decisions)
Settings: decisions 1-31 Jan 2026, cut-off 10:00 Europe/London, delivery on the next day, hourly alignment, 2-day lookback.
- 744 of 744 hourly intervals matched.
- MAE 2,013 MW, RMSE 2,505.9 MW, bias +1,729.9 MW (error = forecast - actual; positive means the forecast was too high).
- The forecast was above the actual in about 84% of intervals (computed from the CSV export). The cause has not been investigated.
- Worst days by MAE: 27 Jan, 11 Jan, 10 Jan.

What was checked, and what was not, is recorded in `VALIDATION.md`. Requirement status is in `REQUIREMENTS_MAP.md`.

## Features
- Single decision, custom January range, or full January.
- Background jobs with day-by-day progress and clear source failures.
- MAE, RMSE, bias, expected/matched coverage, daily and aggregate metrics.
- Forecast vs actual chart, error chart, biggest misses, searchable and filterable audit table.
- Interval provenance dialog, raw source previews, request parameters and diagnostics.
- JSON and CSV export; dark and light appearance; responsive layout.
- Bounded publication windows, retry with backoff, 24-hour cache of real responses.

## Requirements
Python 3.11+ (3.12 recommended), Node.js 22 and npm. Tested with Python 3.14.2 locally and Python 3.12 in Docker. Internet access is needed for installing packages and for live Elexon data.

## Run with Docker (easiest)
Needs Docker Desktop running. From the project root:
```sh
docker compose -f docker-compose.full.yml up --build
```
Open http://localhost:5173 (frontend). The API runs at http://localhost:8000. The first build takes several minutes. Stop with Ctrl+C.
`docker-compose.yml` starts the backend only. The frontend image is built with the backend address as the build argument `VITE_API_BASE_URL` (default `http://localhost:8000`).

## Run locally without Docker
Terminal 1 (backend), from the project root:
```sh
cd backend
python -m venv .venv
```
Activate the environment (Windows PowerShell: `.\.venv\Scripts\Activate.ps1`; macOS/Linux: `source .venv/bin/activate`), then:
```sh
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000 --workers 1
```
Health: http://localhost:8000/api/health. Interactive API docs: http://localhost:8000/docs.

Terminal 2 (frontend):
```sh
cd frontend
npm install
npm run dev
```
Open http://localhost:5173. Start with Single day, 10 January, 10:00, **Hourly** alignment and a 2-day lookback, then click Run analysis. Use Full January after one day works.

Tests: `python -m pytest -q` (backend, environment active) and `npm run build` (frontend).

## Folder structure
```
backend/app/engine.py            forecast selection, matching, conflict handling, metrics
backend/app/source.py            Elexon requests, retries, cache
backend/app/main.py              validation, jobs, progress, exports
backend/app/verify_live.py       live validation helper
backend/tests/                   engine and mocked integration tests
backend/Dockerfile               API image
frontend/src/main.jsx            React views and user flow
frontend/src/style.css           responsive dual-theme UI
frontend/Dockerfile              builds the app, serves it with nginx
frontend/nginx/                  nginx config template
docker-compose.yml               backend only
docker-compose.full.yml          backend + frontend
VALIDATION.md, REQUIREMENTS_MAP.md
```

## API
`POST /api/jobs` with JSON:
```json
{"start_date":"2026-01-01","end_date":"2026-01-31","cutoff_time":"10:00","alignment":"exact","lookback_days":2}
```
- `GET /api/jobs/{id}`: status and completed days.
- `GET /api/jobs/{id}/result`: complete or partial report.
- `GET /api/jobs/{id}/export.csv`: full loaded report.
- `GET /api/health`: backend health only; it does not prove Elexon is reachable.

## Data sources
- https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream
- https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream
- API base: https://data.elexon.co.uk/bmrs/api/v1 (no API key)

WINDFOR uses `publishDateTimeFrom/To`. FUELHH uses `settlementDateFrom/To` and `fuelType=WIND`.

## Assumptions and policies
1. Decision dates are 1-31 January 2026 in Europe/London. Delivery is the next calendar day, so 31 January uses 1 February. All joins are normalised to UTC.
2. The default 10:00 cut-off is editable and is **not** an official market gate closure.
3. For each delivery time, the latest forecast with `publishTime` <= cut-off is selected independently. Several publications may contribute to one delivery day.
4. Forecast search is limited to `lookback_days` (1-7, default 2) before the cut-off.
5. **Exact mode** compares identical timestamps on a 30-minute grid and does not interpolate. In the records checked, WINDFOR values are on the hour only, so exact mode has 50% coverage by design (24 of 48 on 10 Jan).
6. **Hourly mode** treats the forecast on the hour as that hour's average MW and compares it with the mean of the two half-hour actuals (both must exist). This is an explicit modelling assumption, used for the reported results because the forecasts are hourly. Off-hour forecasts are counted in diagnostics, never silently shifted.
7. FUELHH values are average MW over half hours, not MWh. The app evaluates MW errors, not costs.
8. The latest returned actual revision is used.
9. Same delivery and publication timestamp with identical values is deduplicated. Conflicting values are excluded and flagged.
10. Non-finite, negative, boolean or null generation values are invalid; zero is valid.
11. error = forecast - actual. MAE = sum(abs(error))/matched; RMSE = sqrt(sum(error^2)/matched); bias = sum(error)/matched. Period metrics are computed across matched intervals, not as averages of daily averages.
12. All requested delivery intervals count toward coverage, including days where the source failed. Failures are shown, never replaced with fake data.

## User flow
1. Define scope, cut-off, alignment and lookback, then Run analysis.
2. Overview: forecast vs actual and the daily summary.
3. Accuracy lab: error chart and largest misses.
4. Data explorer: filter, search and inspect the provenance of each interval.
5. Methodology: source diagnostics and requests; export CSV or JSON.

Changing controls does not change an already loaded report until Run analysis is clicked.

## Live validation helper
From `backend`, with the environment active:
```sh
python -m app.verify_live --date 2026-01-10
```
It fetches real records and saves `live-validation.json` with previews, requests and metrics, and checks the cut-off mechanically.

## Deployment
- **Backend (Heroku, Docker):** from `backend`, `heroku create <name>`, `heroku container:push web -a <name>`, `heroku container:release web -a <name>`, then `heroku ps:scale web=1`. Jobs live in memory, so run exactly one process and one worker.
- **Frontend (Vercel):** import the repository, set Root Directory to `frontend` (build `npm run build`, output `dist`) and set `VITE_API_BASE_URL` to the backend HTTPS origin without `/api`. Rebuild after changing it.
- **CORS:** set the backend variable `ALLOWED_ORIGINS` to the exact HTTPS frontend origin: `heroku config:set ALLOWED_ORIGINS=https://<app>.vercel.app -a <name>`.
- The backend can restart and lose jobs and the cache; re-run the analysis if that happens.

## Limitations
Job state and reports live in memory, expire after two hours when new jobs arrive, and are lost on restart. One analysis runs at a time per server, with one worker. A production system would need a durable queue, a database, authentication and distributed rate limiting. The cache holds public source records and is ephemeral unless a volume is mounted. This is a time-boxed assessment application, not trading infrastructure: no execution, no price optimisation and no new forecasting model.

## AI assistance disclosure
AI tools were used in this project: Perplexity AI for the initial scaffolding (React UI, Python integration, tests, documentation), and Claude (Anthropic) for the frontend Docker setup, deployment and Git guidance, and reviewing my validation results. I ran the backend tests and the frontend build, ran the app in Docker, executed live analyses (single day and full January), exported the CSV and recalculated the metrics independently, and compared the app's values with raw Elexon API records by hand. [Add anything you changed in the code yourself, or delete this sentence.]
