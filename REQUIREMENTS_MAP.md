# Assessment requirement map

| Requirement | Implementation | Status / evidence |
|---|---|---|
| React frontend | Dashboard, accuracy lab, data explorer, methodology | Done: `npm run build` passes; checked in browser and in Docker |
| Python backend | FastAPI background analysis API | Done locally and in Docker; deployment pending |
| Elexon actual WIND | FUELHH stream client, `fuelType=WIND` | Done: raw 2 Jan 00:00-03:00 UTC values match the app (see VALIDATION.md) |
| Elexon forecasts | WINDFOR publication-window client | Done: raw 09:30 UTC run of 1 Jan matches the app; forecasts are hourly |
| Latest forecast available at decision | Latest `publishTime` <= cut-off, per delivery time | Done: 744 of 744 exported rows have a publish time at or before the cut-off; one day checked by hand |
| Quantitative accuracy | MAE, RMSE, bias, coverage, per-interval errors | Done: dashboard matches independent CSV recalculation |
| January 2026 decisions | Day, range and full-month modes; next-day delivery | Done: 744 of 744 intervals matched for decisions 1-31 Jan |
| Docker | Backend Dockerfile; frontend Dockerfile with nginx; `docker-compose.full.yml` | Done: both services started and the app ran on Windows |
| Hosted working app | Heroku (backend) + Vercel (frontend) | **Pending**: not deployed yet |
| Public anonymous repository and README | Source tree + README | **Pending**: repository not created yet |
| Unlisted two-part video | Script prepared | **Pending**: not recorded |
| Submission form | - | **Pending** |
