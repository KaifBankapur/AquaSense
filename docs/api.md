# AquaSense — REST API reference

Base URL: `/api` (dev: `http://127.0.0.1:8000/api`; compose: `http://localhost:8000/api`)

Interactive docs: `http://127.0.0.1:8000/docs` (Swagger) · `/redoc` (ReDoc)

All responses are JSON. Endpoints read the Parquet analytical layer produced by
the Spark pipeline; if it is missing they return `503 {"detail": ...}`.

---

## System

### `GET /api/health`
```json
{ "status": "ok", "service": "Smart Water Consumption Analytics",
  "version": "1.0.0", "spark": "4.2.0", "dataset_present": true }
```

### `GET /api/pipeline`
Pipeline metadata written by the last Spark run:
`ran_at`, `cluster {app_name, master, version, default_parallelism, spark_ui}`,
`stage_times_seconds`, `total_seconds`, `processed_records`, `areas`,
`outputs {clean_parquet, analytics, analytics_files}`.

### `GET /api/dataset/info`
The generator's `generation_report.json`: seed, target rows, households, months,
date range, rows written, columns, file path, `synthetic_demo_data`.

---

## Dashboard

### `GET /api/dashboard/summary`
```json
{ "total_supplied_liters": 13768722.4, "total_consumed_liters": 13146155.2,
  "total_wastage_liters": 622567.2, "wastage_rate_pct": 4.52,
  "peak_consumption_liters": 522.0, "peak_hour": 19,
  "active_areas": 10, "record_count": 350400, "date_range": ["2025-09-24","2026-09-23"] }
```

### `GET /api/dashboard/kpis`
Six KPI cards `{key,label,value,unit,icon,sparkline}`:
`total_consumption` (last-30-day sparkline), `total_supplied`, `total_wastage`,
`wastage_rate`, `peak_consumption`, `active_areas`.

### `GET /api/dashboard/trend`
Query params:

| param | values |
|---|---|
| `granularity` | `hourly` \| `daily` \| `weekly` \| `monthly` \| `yearly` (default `daily`) |
| `from_date`, `to_date` | ISO dates `YYYY-MM-DD` |
| `area_id` | single area filter |
| `building_type` | single building-type filter |

Returns `{granularity, points: [{label, consumed, supplied, wastage}, ...]}`.

---

## Areas

### `GET /api/areas`
`{ areas: [{area_id, area_name, zone, population, total_supplied_liters,
total_consumed_liters, wastage_liters, wastage_rate_pct, share_pct,
peak_hour, peak_liters, rank}], count }` — ranked by consumption.

### `GET /api/areas/{area_id}`
Area detail: `area`, `totals`, `trend_daily`, `trend_monthly`, `profile_hourly`,
`anomaly_count`, `wastage`, `forecast {method, points}`, `leak_events`.
404 for unknown `area_id`.

### `GET /api/areas/compare?area_ids=A1,A2`
Side-by-side comparison `{areas: [...], count}`.

### `GET /api/areas/top-consumers?limit=10`
Top households by consumption.

---

## Wastage

### `GET /api/wastage`
`{ total_supplied_liters, total_consumed_liters, total_wastage_liters,
wastage_rate_pct, leak_event_count (threshold_pct window), by_area: [{area_id,
area_name, wastage_liters, wastage_rate_pct}], top_10_households }`.

### `GET /api/wastage/areas`
`{ areas: by_area, count }`.

### `GET /api/wastage/leaks`
`{ leak_events: [...], leak_event_count, threshold_pct }`.

---

## Peak analysis

### `GET /api/peak`
Daily + hourly peak profile:
`{ peak_hour, peak_day, by_hour: [{hour, liters}], by_day: [...] }`.

---

## Forecast

### `GET /api/forecast`
`{ method: "seasonal_linear_regression (Spark ML)", model_metrics: {rmse: 3494.1,
mae: 2824.85, ...}, forecast_7d: {points: [...7 days]}, forecast_30d: {
points: [...30 days]}, history, ema_history }`.
Each point is `{date, predicted, lower, upper}`; values are model predictions,
clearly labelled as such.

---

## Anomalies

### `GET /api/anomalies`
Query params: `area_id` (comma-separated), `from_date`, `to_date`, `severity`
(`ANOMALY|HIGH|POSSIBLE_LEAKAGE|NORMAL`), `building_type` (comma-separated),
`page` (default 1), `page_size` (default 50, max 200).

```json
{ "events": [ { "timestamp": "2026-03-14T04:00:00", "area_id": "A3",
                "area_name": "Gokul Road", "zone": "South",
                "household_id": "H00021", "building_type": "residential_flat",
                "anomaly_class": "HIGH", "severity": "medium",
                "consumed_water_liters": 17.9, "rolling_mean": 5.6,
                "rolling_std": 1.1, "deviation_pct": 218.4, "z_score": 4.7,
                "wastage_percent": 0.0 } ],
  "total": 7226, "total_flagged": 7226, "page": 1, "page_size": 50,
  "counts": {"ANOMALY": 21, "HIGH": 6808, "POSSIBLE_LEAKAGE": 397},
  "severity_counts": {"critical": ..., "high": ..., "medium": ...},
  "by_area": [...10 areas...] }
```

**`total_flagged` = `ANOMALY` + `HIGH` + `POSSIBLE_LEAKAGE`** — `NORMAL` rows are
never counted as flags (7,226 flagged hours out of 350,400 in the seed-42 run).

### `GET /api/anomalies/summary`
`{ counts, total_flagged, severity_counts, by_area }` (paginated internally, no
`NORMAL` inflation).

---

## Data explorer

### `GET /api/data`
Query params: `page`, `page_size` (max 100), `search` (text search across
household/area), `sort_by`, `sort_desc`, `from_date`, `to_date`, `area_id`,
`building_type`, `zone`, `meter_status`.
`{ total, page, page_size, rows: [...] }`.

### `GET /api/data/columns`
`{ columns: [...] }` — names of the explorer columns.

---

## CSV export

### `GET /api/export/csv?resource=areas`
`resource` ∈ `areas | wastage | anomalies | summary | data`.
Optional filters: `area_id`, `from_date`, `to_date`.
Returns `text/csv` with a `Content-Disposition: attachment` header.

---

## AquaAI assistant

### `GET /api/assistant/status`
```json
{ "name": "AquaAI", "mode": "local" | "llm", "llm_configured": true|false,
  "model": "gpt-4o-mini" | null }
```

### `POST /api/assistant/chat`
Body:
```json
{ "content": "Which area wastes the most water?",
  "history": [ { "role": "user", "content": "..." },
               { "role": "assistant", "content": "..." } ] }
```
Response:
```json
{ "message": "…answer…", "mode": "local",
  "tool_calls": [ { "name": "get_wastage_analysis", "arguments": {} } ],
  "suggestions": [ "…", "…", "…" ] }
```
The local router answers from the same tools the API exposes; tool calls are
reported so the UI can render them as chips.