# Smart Water Consumption Analytics — Project Report

**AquaSense** — an end-to-end big-data analytics platform for municipal water
networks. Synthetic hourly meter data → PySpark → Parquet analytical layer →
FastAPI → interactive React dashboard with an AI assistant (AquaAI).

---

## 1. Introduction

Municipal water utilities struggle to turn high-volume, high-velocity meter data
into decisions: *where* water is being wasted, *when* demand peaks, *which*
meters behave abnormally, and *what* next week's demand will look like. This
project builds a complete, working analytics platform around that problem,
demonstrating every stage of a modern big-data pipeline — from data generation
and distributed processing to serving and interactive visualisation.

## 2. Problem statement

- **Volume & velocity:** hourly readings for every household/area quickly
  produce millions of records; answering aggregate questions by hand is
  infeasible.
- **Variety:** raw telemetry is noisy — sensor faults, negative values, missing
  fields — and needs cleaning before analysis.
- **Actionability:** queries like "which area wastes the most water" or "when is
  peak demand" must be answered from *real* processed data, in near real-time,
  with visual and conversational interfaces.

## 3. Objectives

1. Generate a realistic, deterministic, reproducible water-consumption dataset
   at notebook scale (**350 K rows** default, scalable to **millions**).
2. Process it with **Apache Spark (PySpark)**: ingest → clean → detect anomalies
   → forecast → aggregate into an analytical layer (Parquet + JSON).
3. Expose the analytical layer through a **REST API** with filters, pagination,
   CSV export and an AI assistant.
4. Build a **dashboard** where every number, chart and answer is computed by the
   pipeline — nothing fabricated, honest empty states when data is absent.

## 4. Methodology

### 4.1 Dataset generation (`scripts/generate_dataset.py`)

A seeded (`seed=42`) generator produces realistic hourly readings: diurnal
profiles with morning/evening peaks, weekday/weekend and seasonal factors,
temperature and rainfall effects, building-type multipliers, meter bias/faults,
and occasional leakage windows and consumption spikes. 10 areas modelled on
Hubballi-Dharwad neighbourhoods; 40 households distributed proportional to
population (total 350,400 rows; 20 columns). `--rows`/`--households`/`--months`
scale the experiment.

### 4.2 Big-data pipeline (`bigdata/spark/`, PySpark 4.2, `local[*]`)

| Stage | Module | Work |
|---|---|---|
| Ingest | `ingestion/ingest.py` | strict typed CSV read |
| Preprocess | `preprocessing/preprocess.py` | null/`area_id` filtering, negative-value fixes, `consumed ≤ supplied` checks |
| Quality | `preprocessing/quality.py` | records read/valid/invalid, per-column nulls, duplicates |
| Analytics | `analytics/*.py` | totals, areas (ranked), peaks, wastage, households, time-series → 9 JSON artifacts + Parquet |
| Anomalies | `anomaly_detection/detect.py` | per-property rolling Z-score + deviation classification (`ANOMALY`/`HIGH`/`POSSIBLE_LEAKAGE`/`NORMAL`) |
| Forecast | `forecasting/forecast.py` | **seasonal linear regression** (Spark ML) — daily series → 7-day and 30-day forecasts + RMSE/MAE |

`pipeline_meta.json` records stage timings, processed records and artifact list.

### 4.3 API layer (FastAPI)

REST endpoints under `/api` (OpenAPI at `/docs`) read the Parquet analytical
layer (PyArrow) — dashboard summary/KPIs/trends, areas + detail + comparison,
wastage, peaks, forecast, anomalies with pagination/filters, data explorer,
CSV export, pipeline status, and the AquaAI chat endpoint. Local development uses
SQLite; `docker-compose` swaps in Postgres. Missing data → `503` with honest
empty states in the UI.

### 4.4 AquaAI (assistant-ui + tool calling)

- Without an API key: a deterministic **local intent router** answers questions
  by resolving intents to the same data-backed tools the REST API exposes
  (wastage, compare areas, anomaly counts, peaks, total consumption, forecast),
  reporting the tool calls it made.
- With `AQUA_LLM_API_KEY`: an OpenAI-compatible LLM receives tool results and
  answers conversationally, with chat history.

### 4.5 Frontend (React 18 + TypeScript + Vite)

11 pages (Dashboard, Areas + detail, Wastage, Peak, Anomalies, Forecast, Data
Explorer, Pipeline, AI Assistant, About) backed by recharts visualisations,
Tailwind (v3, class-based dark mode), shadcn-style components, CSV export, and
an assistant-ui chat runtime streaming answers from `/api/assistant/chat`.

## 5. Results (seed 42, 350,400 rows)

Measured from the live analytical layer produced by the final pipeline run
(2026-09-23, Spark 4.2.0, `local[*]`):

- **Dataset:** 350,400 hourly records · 40 households · **10 areas** · 12
  months (2025-09-24 → 2026-09-23) · seed 42 · fully reproducible.
- **Data quality:** 350,400/350,400 records valid after preprocessing
  (`valid_records + invalid_records == total_records_read`, `invalid == 0`).
- **Totals:** 13,768,722 L supplied · 13,146,155 L consumed ·
  **622,567 L wasted (4.52 %)**.
- **Anomalies:** **7,226 flagged hours** = `ANOMALY` 21 + `HIGH` 6,808 +
  `POSSIBLE_LEAKAGE` 397; NORMAL (343,174 rows) excluded from all flagged
  totals; every event carries timestamp, area, household, expected vs actual
  volume, deviation% and z-score.
- **Peak:** single deterministic **19:00** peak hour (1,037,451 L/h across the
  network), Monday as peak weekday, May 2026 as peak month; every area also
  peaks at 19:00.
- **Wastage:** 397 leak events (wastage ≥ 15 % threshold), per-area rates
  ranking Industrial Area (A10, 6.17 %) as least efficient and Old Hubballi
  (A6, 3.73 %) most efficient.
- **Forecast:** Spark ML **seasonal linear regression** (day-index + 7d/365d
  seasonal features) fit on 365 daily points → RMSE ≈ 3,494 L/day, MAE ≈
  2,825 L/day; **7-day and 30-day forecasts with confidence bands**.
- **Performance:** full pipeline (Spark stage time ≈ 250 s ≈ 4.2 min wall clock
  on a laptop, `local[*]`, 12 cores); per-stage timings logged in
  `pipeline_meta.json`.

## 6. Testing & validation

- **Backend:** `pytest tests` — API contract tests against the **real Parquet
  analytical layer** (shapes, counts, 10 areas, peak hour, flagged-only anomaly
  totals) + intent-router unit tests (13 assistant questions, plus smoke).
- **Frontend:** vitest (formatting + component tests) and a production
  `tsc --noEmit && vite build`.
- **Assistant smoke:** `tests/smoke_assistant.py` asks AquaAI a battery of
  questions and asserts the answers are data-backed.
- **Human QA:** live spot-check of every page against the running API (dark
  mode, filters, export, chat).

## 7. Conclusions

AquaSense demonstrates a complete, working big-data stack for time-series
telemetry on commodity hardware: deterministic synthetic data → Spark
processing → analytical layer → API → dashboard + assistant. The key design
decision — analytics are **computed once by Spark** and **served from the
analytical layer**, never derived at request time — keeps every chart truthful,
fast, and decoupled from the raw data volume. The deterministic local assistant
shows how "AI" can be genuinely data-backed without a model, while the LLM path
upgrades it to natural-language conversation when a key is configured.

## 8. Future work

- Stream ingestion (Kafka/Kinesis) instead of batch CSV.
- Sliding-window anomaly detection on live telemetry.
- Gradient-boosted forecasting vs the Spark ML baseline.
- Multi-user auth + role-based area scoping.
- Real or open municipal datasets to replace the synthetic layer.

---

*All data is synthetic demo data. No real government records are involved.*