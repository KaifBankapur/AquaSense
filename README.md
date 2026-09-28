# AquaSense — Smart Water Consumption Analytics

A complete big-data analytics platform for municipal water networks.

**Pipeline:** synthetic hourly water-meter data → **PySpark** (cleaning, anomaly detection, forecasting) → **Parquet analytical layer** → **FastAPI** → **React dashboard** with an AI assistant (AquaAI).

```
synthetic data (CSV) ──▶ PySpark ──▶ Parquet + JSON analytics ──▶ FastAPI ──▶ React (Vite, TS)
                              bigdata/                       backend/         frontend/
```

Everything you see on screen is **real analytics computed by Spark** — no fabricated
numbers, no stubbed charts. The dataset is synthetic (seeded, reproducible) because
real municipal meter data is not public; the *processing* is genuine end-to-end big data.

---

## Highlights

| Layer | Stack | Deliverable |
|---|---|---|
| Data | Seeded synthetic generator (`random.Random`, seed 42) | 350,400 hourly records · 40 households · 10 areas |
| Big data | PySpark 4.2 · Spark SQL DataFrames · Parquet | Clean layer + 9 analytics artifacts |
| Analytics | Z-score anomaly detection, seasonal linear regression forecast, wastage/peak/time-series aggregation | `bigdata/outputs/analytics/*.json` |
| API | FastAPI + SQLAlchemy (SQLite or Postgres) | REST under `/api`, OpenAPI at `/docs` |
| Frontend | React 18 · TypeScript · Vite · Tailwind v3 · shadcn-style UI · recharts · assistant-ui | 12 pages, dark-first theme, CSV export |

Dashboard UI detail — the dashboard opens with an animated **hero** (orbiting water core + glow gradients, designed after 21st.dev *Hero Section 06*/*Advanced Stats*), **Vengeance UI** text animations (Stagger Text headline, Flip Text subtitle, Morph Text focus word, Animated Number stat chips), all fed by the live API. Component sources: [21st.dev](https://21st.dev) (design language, metadata + code retrieved via MCP) and [Vengeance UI](https://www.vengenceui.com) (public shadcn registry).

Landing UI detail — `/` is a dark, self-contained marketing page built from the 21st.dev *SaaS Template* (fixed blurred nav, gradient headline, announcement pill, dual CTAs). The template's stock preview art was replaced with a **Tailwind-built dashboard mockup** (window chrome, mini sidebar, KPI tiles, wastage-rate bar chart) behind a cyan glow, so the landing ships with zero external image dependencies.

Two [React Bits](https://reactbits.dev) components are integrated on that page, both in `src/components/ui/` and both TypeScript ports rather than verbatim copies:

| Component | Dependency | Where | Notes |
|---|---|---|---|
| `scroll-reveal.tsx` | `gsap` | statement band under the hero | Words un-blur and de-rotate on scroll |
| `electric-logo.tsx` | `ogl` | nav brand mark (traces `public/aqua-mark.svg`) | WebGL2 electric-strand logo |

Each carries fixes over the upstream source, in case the vendor copy is ever re-synced: `ScrollReveal` scopes its triggers with `gsap.matchMedia()` instead of `ScrollTrigger.getAll().kill()` (which would tear down unrelated triggers), honours `prefers-reduced-motion` by creating no triggers at all, and renders element children instead of discarding them; `ElectricLogo` guards WebGL2 construction so a missing context degrades to an empty container rather than throwing, and feature-detects `IntersectionObserver`.
| AI | assistant-ui chat + tool calling; LLM (OpenAI-compatible) **or** deterministic local intent router | AquaAI answer-station |

### Pages

`/` Landing (dark SaaS template — nav + hero + dashboard preview mockup) ·
`/dashboard` Dashboard (KPI cards + trends + filters) · `/areas` + area detail ·
`/wastage` · `/peak` Peak Analysis · `/anomalies` · `/forecast` ·
`/data` Data Explorer · `/pipeline` Spark pipeline status ·
`/assistant` AquaAI · `/about`. `/landing` redirects to `/`; unknown routes fall
back to `/dashboard`.

---

## Quick start (local)

### 1. Prerequisites (Windows)

- Python 3.14 (`py -3.14`)
- JDK 17 (Temurin) — required by PySpark
- Hadoop helpers for Windows: `winutils.exe` in `tools/hadoop/bin` (see `scripts/setup.py`)
- Node 18+ (for the frontend)

```powershell
# one-time environment check / install
py -3.14 scripts/setup.py --check
py -3.14 scripts/setup.py --install     # pip install + writes .env defaults
```

### 2. Generate data + run the Spark pipeline (≈4–5 min)

```powershell
# sets JAVA_HOME / HADOOP_HOME / PYSPARK_PYTHON for this shell.
# PYSPARK_PYTHON must be the FULL path to a python.exe (no arguments) —
# PySpark launches worker processes directly and cannot run "py -3.14".
$PY = (py -3.14 -c "import sys; print(sys.executable)")
$env:JAVA_HOME='C:\Users\<you>\AppData\Local\Programs\Temurin17\jdk-17.x'
$env:HADOOP_HOME='E:\AquaSense\tools\hadoop'
$env:PATH="$env:HADOOP_HOME\bin;$env:JAVA_HOME\bin;$env:PATH"
$env:PYSPARK_PYTHON=$PY

py -3.14 scripts/run_pipeline.py            # default dataset (350,400 rows)
py -3.14 scripts/run_pipeline.py --rows 1000000   # scale to ~1M rows
py -3.14 scripts/run_pipeline.py --households 600 --months 12 --seed 7
py -3.14 scripts/run_pipeline.py --skip-generate  # reuse existing CSV
```

### 3. Start the backend

```powershell
py -3.14 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
# API docs: http://127.0.0.1:8000/docs
```

### 4. Start the frontend

```powershell
cd frontend
npm install
npm run dev          # http://localhost:5173  ->  landing page
                      # http://localhost:5173/dashboard
```

Vite binds to IPv6 `localhost` only — use `localhost`, not `127.0.0.1`.

The Vite dev server proxies `/api` → `127.0.0.1:8000`, so no CORS config is needed
in development.

---

## Tests

```powershell
# backend: hits the real Parquet analytical layer end-to-end
py -3.14 -m pytest tests -q

# frontend
cd frontend && npm test          # vitest
npm run build                    # typecheck + production build
```

### AI assistant modes

- **`local` (default, no API key):** deterministic intent router + data-backed answers
  via the same tools the API exposes. Works offline, never fabricates numbers.
- **`llm`:** set `AQUA_LLM_API_KEY` in `.env` (OpenAI-compatible base URL + model).
  The LLM receives tool-call results and answers in natural language.
- **`auto`:** LLM if a key is present, otherwise local.

---

## Docker (Postgres + API + SPA)

```bash
docker compose up --build
# frontend  http://localhost:8080
# API       http://localhost:8000/docs
```

Notes:

- The backend container **mounts `./bigdata`** so it serves whatever analytical layer
  the host generated. To have data in the container, run the pipeline on the host
  **before** `docker compose up` (PySpark on Windows needs JDK + winutils; running the
  pipeline itself inside the container is optional — see `bigdata/` docs).
- Postgres replaces SQLite inside the compose stack via
  `AQUA_DATABASE_URL=postgresql+psycopg2://aqua:aqua@postgres:5432/aqua`.
- Without a generated dataset the dashboard shows honest empty states instead of
  fabricated charts.

---

## Repository layout

```
E:\AquaSense\
├── bigdata/
│   ├── data/raw/                     # generated CSV + generation report
│   ├── data/processed/               # consumption_clean/ + anomalies/ (Parquet)
│   ├── outputs/analytics/            # 9 JSON artifacts consumed by the API
│   ├── spark/                        # ingestion, preprocessing, analytics,
│   │                                 # anomaly detection, forecasting (PySpark)
│   └── jobs/run_analytics.py         # run analytics directly against Parquet
├── backend/
│   └── app/                          # FastAPI app (api/, services/, ai/, core/)
├── frontend/                         # React + Vite SPA
├── scripts/                          # generate_dataset.py, run_pipeline.py, setup.py
├── tests/                            # backend pytest suite + assistant smoke test
├── docs/                             # architecture, API, dataset, project report
├── docker-compose.yml
└── .env.example
```

---

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — components, data flow, pipeline stages
- [`docs/api.md`](docs/api.md) — every REST endpoint and its response shape
- [`docs/dataset.md`](docs/dataset.md) — data model, generator, scaling to millions
- [`docs/project-report.md`](docs/project-report.md) — academic project report

## Disclaimer

All data is **synthetic demo data** generated with a deterministic seed. It models
Hubballi-Dharwad area structure for realism but contains no real government records.