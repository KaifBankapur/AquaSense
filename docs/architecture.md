# AquaSense — Architecture

## System overview

```
┌────────────────────────────────────────────────────────────────────┐
│  DATA LAYER      scripts/generate_dataset.py (seeded, synthetic)  │
│                  bigdata/data/raw/consumption_hourly.csv          │
│                  (timestamp, area, household, supplied/consumed,  │
│                   temperature, rainfall, pressure, meter_status)  │
└───────────────────────────────┬────────────────────────────────────┘
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│  BIG-DATA LAYER    PySpark 4.2 (local[*], Spark SQL DataFrames)   │
│                                                                    │
│  1. ingestion     CSV → typed DataFrame (20 columns, schema in    │
│                   bigdata/spark/ingestion/ingest.py)              │
│  2. preprocessing quality/dedup/type-casts/negative-value fixes   │
│                   → bigdata/data/processed/consumption_clean/     │
│  3. analytics     totals · areas · peaks · wastage · households · │
│                   time-series  → 9 JSON artifacts + Parquet       │
│  4. anomaly       per-property Z-score + deviation rules on       │
│     detection      rolling windows → ANOMALY / HIGH /             │
│                   POSSIBLE_LEAKAGE / NORMAL                       │
│  5. forecasting   seasonal linear regression (Spark ML)           │
│                   → 7d / 30d forecasts + RMSE                     │
└───────────────────────────────┬────────────────────────────────────┘
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│  SERVICE LAYER    FastAPI (backend/app/)                           │
│                   • analytics/store.py   : reads Parquet + JSON    │
│                   • services/            : aggregation, export     │
│                   • ai/                  : AquaAI (LLM or local)   │
│                   • core/database.py     : SQLAlchemy (SQLite /    │
│                                            Postgres via compose)   │
└───────────────────────────────┬────────────────────────────────────┘
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│  PRESENTATION     React 18 + TypeScript + Vite                     │
│                   Tailwind v3 · shadcn-style components · recharts │
│                   assistant-ui chat (useExternalStoreRuntime)      │
│                   Pages: Dashboard, Areas, Wastage, Peak,          │
│                   Anomalies, Forecast, Data Explorer, Pipeline,    │
│                   About, AI Assistant                              │
└────────────────────────────────────────────────────────────────────┘
```

## Component responsibilities

### `scripts/generate_dataset.py`

Deterministic, domain-realistic synthetic generator.

- 10 areas modelled on Hubballi-Dharwad neighbourhoods, each with population,
  zone, industrial factor and base per-capita litres (`AREAS`, 10 entries).
- Buildings distributed by type weights (residential/commercial/industrial/
  institutional) with member counts per household.
- Hourly consumption = per-capita base × diurnal profile × weekday/weekend factor
  × monthly seasonality × weather (temp drives up, rain suppresses) × noise.
- Leakage windows and abnormal spikes are injected at low, profile-driven rates;
  metering faults and pressure are realistic.
- `--rows N` derives the household count; `--households`/`--months`/`--seed`
  give explicit control (see `docs/dataset.md`).

### Big-data layer (`bigdata/spark/`)

- `ingestion/ingest.py` — strict CSV schema (`timestamp`, `date`, `hour`,
  `day_of_week`, `weekday`, `month`, `year`, `area_id`, `area_name`, `zone`,
  `household_id`, `building_type`, `population`, `supplied_water_liters`,
  `consumed_water_liters`, `wastage_liters`, `temperature_c`, `rainfall_mm`,
  `pressure_bar`, `meter_status`).
- `preprocessing/preprocess.py` — drops nulls/malformed `area_id`, fixes
  negatives, coerces types; keeps only rows where `consumed <= supplied`.
- `preprocessing/quality.py` — data-quality report (records read, valid,
  invalid, per-column nulls, duplicate count).
- `analytics/*.py` — Spark SQL `groupBy`/`agg` computations producing the 9
  JSON artifacts (`summary`, `areas`, `peaks`, `wastage`, `households`,
  `time_series`, `anomalies`, `forecast`, `data_quality`).
- `anomaly_detection/detect.py` — per-property rolling statistics; an hour is
  flagged when its deviation exceeds the per-property threshold, classified by
  severity. `NORMAL` records are excluded from flagged totals everywhere.
- `forecasting/forecast.py` — Spark ML seasonal linear regression fit on the
  daily series, `forecast_7d`/`forecast_30d` + `model_metrics.rmse`.
- `context.py` / `pipeline.py` — SparkSession factory (local[*], Arrow enabled)
  and orchestration with per-stage timing written to `pipeline_meta.json`.

### Backend (`backend/app/`)

| Module | Purpose |
|---|---|
| `api/router.py` | mounts all route modules under `/api` |
| `api/routes/*` | dashboard, areas, wastage, peak, forecast, data-quality, anomalies, data explorer, CSV export, assistant, health/pipeline |
| `analytics/store.py` | loads Parquet via PyArrow; caches; `DatasetUnavailableError` → API returns 503 |
| `services/analytics_service.py` | all JSON/Parquet-backed aggregations (filters, paging, area detail, comparisons) |
| `services/export_service.py` | streams CSV for `areas|wastage|anomalies|summary|data` |
| `ai/` | AquaAI: `intents.py` (local router), `llm.py` (OpenAI-compatible), `tools.py` (data-backed tool registry), `service.py` (dispatch) |
| `core/config.py` | pydantic-settings, env-driven (`AQUA_*`, `.env`) |
| `core/database.py` | SQLAlchemy engine; SQLite locally, Postgres via compose |

### Frontend (`frontend/`)

- `src/lib/api.ts` — typed fetch client; in dev the Vite proxy sends `/api` to
  `127.0.0.1:8000`, so no CORS is needed; in production the built SPA is served
  by nginx which proxies `/api` to the backend.
- `src/hooks/useApi.ts` — fetch + loading/error/retry state.
- `src/pages/*` — one page per analytics domain; every chart is fed by live API
  data (recharts), with `LoadingState` / `ErrorState` / `EmptyState` components.
- `src/assistant/runtime.ts` — assistant-ui `useExternalStoreRuntime` wired to
  `/api/assistant/chat`; mode badge, suggestion chips and tool-call chips.
- Dark/light theme via class-based Tailwind (v3 mode), persisted toggle.

## Data flow guarantees

1. The API **never computes analytics from the raw CSV** at request time — it
   reads the Parquet analytical layer produced by Spark, so every chart is a
   genuine pipeline result.
2. All artifacts are written by `run_pipeline.py`; `pipeline_meta.json` records
   stage timings, record counts and the artifact list.
3. When the analytical layer is absent the API returns `503` and the UI renders
   empty states — no fabricated placeholder charts.

## Scaling

`--rows`/`--households` scale the dataset up to millions of records; the
pipeline is DataFrame-based (no `rdd` worker paths) and runs on a laptop
(`local[*]`). Larger runs only increase run time (see `docs/dataset.md` for
measured timings and a cost table).