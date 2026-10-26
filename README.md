# WindLens - historical UK wind forecast intelligence

A React + Python/FastAPI web application for exploring historical UK wind forecasts with Elexon BMRS data. It answers:

1. What wind forecast was available at a chosen decision cut-off?
2. How did that forecast compare with actual generation?

The application uses WINDFOR forecasts and FUELHH actuals, with no synthetic-data fallback or invented analytics. It is a time-boxed assessment application, not production trading infrastructure.

## Live deployment

- Live app (Render): https://vrxjszge-1.onrender.com
- Backend API (Render): https://vrxjszge.onrender.com
- Backend health endpoint: https://vrxjszge.onrender.com/api/health
- Interactive API documentation: https://vrxjszge.onrender.com/docs
- Repository: https://github.com/Preethi-CM/vrxjszge
- Demo video: Not yet added.

The frontend is a Render Static Site. The backend is a Docker-based Render Web Service on a free instance. The backend may take time to respond after inactivity. In-memory jobs, reports and ephemeral cache can be lost on restart; re-run the analysis if necessary.

A successful health response checks the backend, not Elexon availability.

## Full-January validation results

The project author confirms that full-January validation was completed and passed. The figures below are the author's reported validation results; they are not presented as an independent third-party audit.

Scenario:

- Decision dates: 1-31 January 2026.
- Decision cut-off: 10:00 Europe/London.
- Delivery: the following calendar day.
- Alignment: hourly.
- Publication lookback: 2 days.

| Measure | Reported result |
| --- | --- |
| Matched hourly intervals | 744 of 744 |
| Matched coverage | 100% |
| MAE | 2,013 MW |
| RMSE | 2,505.9 MW |
| Forecast bias | +1,729.9 MW |

Error is forecast minus actual, so positive bias means overforecasting. These results apply to hourly alignment, not exact alignment on a 30-minute grid. The 31 decision dates cover the following delivery days, including 1 February for the 31 January decision.

The author's earlier validation summary also reported forecasts above actuals in approximately 84% of matched intervals, with 27 January, 11 January and 10 January the worst decision days by MAE. The cause of the overforecasting has not been investigated.

Keep the supporting exports, calculation records and detailed evidence in `VALIDATION.md`. Track assignment requirements separately in `REQUIREMENTS_MAP.md`.

## Deployment checks completed

During deployment, the project author reported completing these checks:

- Ran the application locally with Docker Compose.
- Loaded the deployed frontend in a browser.
- Ran an analysis through the deployed frontend and received results.
- Downloaded a CSV export and checked its data.
- Completed the JSON report check.
- Confirmed that full-January validation passed.

Successful deployment and full-January validation do not automatically establish that every automated test, accessibility check, security check or assignment requirement has passed. Record each check separately.

## Features

- Single decision date, custom January range and full-January evaluation.
- Editable decision cut-off, alignment policy and publication lookback.
- Background jobs with day-by-day progress and explicit source failures.
- MAE, RMSE, forecast bias, expected/matched coverage and daily/aggregate metrics.
- Forecast-versus-actual chart, error analysis and biggest misses.
- Searchable and filterable interval audit data.
- Interval provenance, raw source previews, request parameters and diagnostics.
- JSON and CSV exports.
- Dark/light appearance and responsive layouts.
- Bounded publication windows, retry/backoff and a 24-hour cache of real source responses.

## Technology and requirements

- Frontend: React 18, Vite, Recharts and Lucide React.
- Backend: Python, FastAPI, Uvicorn and HTTPX.
- Containers: Docker and Docker Compose.
- Hosting: Render Static Site and Docker Web Service.

For Docker, install and start Docker Desktop. For development without Docker, use Python 3.11+ (3.12 recommended), Node.js 22 and npm. Internet access is required for dependency installation and live Elexon requests. The backend Dockerfile uses Python 3.12.

## Run with Docker

From the repository root, with Docker Desktop running:

```sh
docker compose -f docker-compose.full.yml up --build
```

Open:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Health: http://localhost:8000/api/health
- API docs: http://localhost:8000/docs

Stop foreground services with `Ctrl+C`. To remove the Compose containers and network:

```sh
docker compose -f docker-compose.full.yml down
```

The full Compose configuration contains:

- `api`: builds from `backend`, exposes port 8000 and mounts `windlens-cache` at `/app/.cache`.
- `web`: builds from `frontend`, uses `VITE_API_BASE_URL=http://localhost:8000` as a build argument and maps local port 5173 to container port 80.

`docker-compose.yml` is the backend-only alternative.

## Run locally without Docker

### Backend

From the repository root:

```sh
cd backend
python -m venv .venv
```

Activate on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Activate on macOS/Linux:

```sh
source .venv/bin/activate
```

Install dependencies and start the API:

```sh
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000 --workers 1
```

If PowerShell blocks activation, use the virtual environment executable directly instead of changing system-wide security settings:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000 --workers 1
```

### Frontend

In another terminal, from the repository root:

```sh
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Start with 10 January, a 10:00 London cut-off and a two-day lookback. Select the alignment explicitly: hourly alignment is used for the full-January results above; exact alignment is a separate timestamp-matching policy.

Changing controls does not update an already loaded report until `Run analysis` is clicked.

## Tests and production build

Backend, from `backend` with its environment active:

```sh
python -m pytest -q
```

Frontend, from `frontend`:

```sh
npm run build
npm run preview
```

If preview uses a different origin, add that exact origin to `ALLOWED_ORIGINS` and restart the backend. Record actual test outputs in `VALIDATION.md`; analysis validation is distinct from automated-test status.

## Configuration

| Variable | Component | Purpose |
| --- | --- | --- |
| `VITE_API_BASE_URL` | Frontend, build time | Backend origin, without an `/api` suffix. |
| `ALLOWED_ORIGINS` | Backend | Comma-separated frontend origins allowed by CORS. |
| `PORT` | Backend | Listening port used by the Docker startup command. |

Deployed frontend setting:

```text
VITE_API_BASE_URL=https://vrxjszge.onrender.com
```

Backend allowed-origin configuration used during deployment:

```text
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://vrxjszge-1.onrender.com
```

Origins should not include paths or trailing slashes. Keep the allowed list limited to intended clients. Rebuild the frontend after changing its API URL.

## Folder structure

```text
backend/
  app/
    engine.py          Forecast selection, matching and metrics
    source.py          Elexon requests, retries and cache
    main.py            API validation, jobs, progress and exports
    verify_live.py     Live validation helper
  tests/               Engine and mocked integration tests
  Dockerfile           Backend image
frontend/
  src/
    main.jsx           React views and user flow
    style.css          Application styles
  Dockerfile           Frontend build and nginx image
  nginx/               nginx configuration
docker-compose.yml         Backend-only local orchestration
docker-compose.full.yml    Backend + frontend local orchestration
VALIDATION.md              Validation evidence and check status
REQUIREMENTS_MAP.md        Requirement tracking
```

## API

Create an analysis with `POST /api/jobs`:

```json
{
  "start_date": "2026-01-01",
  "end_date": "2026-01-31",
  "cutoff_time": "10:00",
  "alignment": "exact",
  "lookback_days": 2
}
```

This example requests exact alignment, not the hourly scenario used for the reported monthly figures. Consult `/docs` for the running API's accepted alignment values and response schemas.

| Endpoint | Purpose |
| --- | --- |
| `POST /api/jobs` | Start an analysis. |
| `GET /api/jobs/{id}` | Read progress and job status. |
| `GET /api/jobs/{id}/result` | Retrieve a complete or partial report. |
| `GET /api/jobs/{id}/export.csv` | Export the loaded report. |
| `GET /api/health` | Check backend health, not upstream availability. |

## Data sources

- FUELHH: https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream
- WINDFOR: https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream
- API base: https://data.elexon.co.uk/bmrs/api/v1

The integration uses `publishDateTimeFrom` / `publishDateTimeTo` for WINDFOR and `settlementDateFrom` / `settlementDateTo` with `fuelType=WIND` for FUELHH. No Elexon API key is configured.

Inspect timestamps, cadence, revisions and diagnostics during validation. Successful retrieval alone does not establish semantic correctness.

## Assumptions and policies

1. Decision dates cover 1-31 January 2026 in Europe/London. Delivery is the next calendar day; a 31 January decision uses 1 February delivery. Joins are normalised to UTC.
2. The editable default 10:00 cut-off is a scenario assumption, not an asserted official market gate closure.
3. For each delivery timestamp, select the latest eligible publication at or before the cut-off. Several publications may contribute to one day; this is not necessarily a single-publication snapshot.
4. Forecast searches are bounded by `lookback_days` (1-7, default 2). Missing records may fall outside that window.
5. Exact alignment compares identical timestamps on a 30-minute expected grid without interpolation. Hourly forecast timestamps can leave half-hour intervals unmatched. The deployed January 10 scenario showed 24 of 48 intervals matched; do not confuse this with the hourly monthly result.
6. Hourly alignment treats a forecast on the hour as that hour's average MW and compares it with the mean of both half-hour actuals; both actuals must exist. This is an explicit modelling assumption. Off-hour forecasts are counted in diagnostics, not silently shifted.
7. FUELHH values are treated as average MW over half hours, not MWh. The application evaluates generation errors, not trading costs.
8. The latest returned actual revision is the retrospective target. Missing actual publication timestamps are not invented.
9. Identical records sharing delivery/publication timestamps are deduplicated. Conflicting values are excluded and flagged rather than resolved arbitrarily.
10. Non-finite, negative, boolean and null generation values are invalid. Numeric zero is valid.
11. Error = forecast - actual. MAE = mean absolute matched error; RMSE = square root of mean squared matched error; bias = mean matched error. Period metrics use all matched intervals, not an unweighted average of daily metrics.
12. All requested delivery intervals count toward coverage, including source-failure days. Failures and missing data are reported, never replaced with synthetic observations.

## User flow

1. Choose a single date, range or full January.
2. Set the cut-off, alignment and lookback.
3. Run analysis and inspect progress or source failures.
4. Review scenario labels, coverage, metrics and charts.
5. Inspect interval provenance, raw records and diagnostics.
6. Export CSV or JSON.

Controls do not alter an already loaded report until another analysis runs. Top-level cards describe the loaded scenario; table/chart filters should not be confused with a different analysis scope.

## Live validation helper

From `backend`, with its environment active:

```sh
python -m app.verify_live --date 2026-01-10
```

The helper fetches real records, writes `live-validation.json` and checks cut-off eligibility mechanically. It does not replace manual source-semantic review. The author's full-January pass confirmation does not, by itself, establish that this particular helper was executed; record its output separately when used.

## Render deployment

### Backend: Docker Web Service

- Branch: `main`.
- Root Directory: `backend`.
- Dockerfile: `Dockerfile` within that root.
- Build context: backend root.
- Instance type used: Free.
- Environment: configure `ALLOWED_ORIGINS` with the exact frontend HTTPS origin.
- Leave the Docker Command override empty to use the Dockerfile startup command.

The Docker startup runs `uvicorn app.main:app` on `0.0.0.0`, uses `${PORT}` and sets `--workers 1`. Deployment logs showed port 10000 and Render reported the service live.

Use exactly one process/worker because jobs live in memory. Do not assume the local Compose cache volume exists on the hosted free service.

### Frontend: Static Site

- Branch: `main`.
- Root Directory: `frontend`.
- Build Command: `npm install && npm run build`.
- Publish Directory: `dist`.
- Environment: `VITE_API_BASE_URL=https://vrxjszge.onrender.com`.

After deploying, include `https://vrxjszge-1.onrender.com` in the backend's `ALLOWED_ORIGINS` and apply that configuration change. Rebuild the frontend when changing its API base URL. Update documentation and environment settings if either public origin changes.

## Validation record and review checklist

Full-January validation is reported passed. Keep the following evidence and individual check statuses in `VALIDATION.md`; do not label every item complete solely from the monthly pass:

- Tested scenario settings, exported rows and independent metric calculations.
- Health endpoint/API docs checks and browser console/network checks.
- Manual forecast selection and error examples, including publication <= cut-off.
- Cadence, UTC offsets, actual revisions and hourly-alignment justification.
- Missing coverage, invalid-record and timestamp-conflict diagnostics.
- January 1 and January 31 boundary-case evidence.
- Source/backend failure behaviour and absence of synthetic fallback.
- Mobile layout, keyboard navigation, dialog dismissal and theme checks.
- Backend test output and frontend production-build output.

Review assignment-specific hosting, repository anonymity, video and submission requirements separately. If particular providers are mandatory, confirm that Render is acceptable or adjust deployment.

## Limitations

- Job state and reports live in memory, expire after two hours when new jobs arrive and are lost on restart.
- One analysis runs at a time per server; one worker is required.
- Cache is ephemeral unless durable storage is explicitly configured.
- Historical completeness, revisions and upstream availability can affect results.
- The free backend may pause after inactivity and has limited resources.
- Production use would need durable jobs, storage, authentication and distributed rate limiting.
- There is no trade execution, price optimisation or new forecasting model.

Validation of the reported scenario does not guarantee future availability or establish production readiness.

## AI assistance disclosure

Perplexity AI assisted with project scaffolding and guidance on React UI, Python integration, tests, documentation, Docker, Render deployment and Git workflow. AI also assisted with consolidating and updating this README.

I ran the application using Docker Compose, deployed the frontend and backend, ran a deployed analysis, checked the CSV export and completed the JSON report check. I also confirm that full-January validation was completed and passed; the reported results are documented above.

These statements do not imply that every automated test, security check or line of code was independently audited. Disclose any additional AI tools and personal contributions accurately if applicable.

## Before submission

- Add the actual demo-video link when available.
- Preserve validation exports, calculations and test evidence.
- Update `VALIDATION.md` and `REQUIREMENTS_MAP.md` with actual check statuses.
- Review the assignment video guide and submission form.
- Respect the assignment's stated 16-hour total effort cap.
- Confirm repository visibility and anonymity requirements.
- Keep all claims limited to work actually performed.
