# AquaSense — Dataset design & scaling

## What the dataset models

`bigdata/data/raw/consumption_hourly.csv` is a synthetic, deterministic series of
**hourly per-meter water readings for 40 households across 10 areas** over 12
months (365 days) of Hubballi-Dharwad-style territory:

| Dimension | Value |
|---|---|
| Rows | 350,400 (= 40 households × 365 days × 24 h) |
| Households | 40 |
| Areas | 10 (`A1`…`A10`) |
| Date range | 2025-09-24 → 2026-09-23 |
| Columns | 20 |
| Seed | 42 (fully reproducible) |
| Format | CSV (Parquet-compatible, UTF-8) |

### Area roster (static metadata in `scripts/generate_dataset.py`)

| id | name | zone | population | industrial factor |
|---|---|---|---|---|
| A1 | Hubballi Central | Central | 125,400 | 1.30 |
| A2 | Vidyanagar | East | 86,400 | 1.15 |
| A3 | Gokul Road | South | 71,200 | 1.10 |
| A4 | Keshwapur | West | 58,200 | 1.05 |
| A5 | Unkal | North-East | 49,300 | 1.00 |
| A6 | Old Hubballi | Central | 112,800 | 1.08 |
| A7 | Dharwad Central | Central | 95,600 | 1.12 |
| A8 | Navanagar | South | 68,400 | 1.25 |
| A9 | Jubilee Circle | West | 42,100 | 1.02 |
| A10 | Industrial Area | Industrial | 18,900 | 2.20 |

Household count is distributed across areas proportional to population
(rounded, with the last area absorbing the remainder so totals are exact —
exercise `_roll_households` for the distribution).

> **Population semantics.** The static roster above is the *reference
> territory* population and is what `/api/areas` reports per area (loaded from
> `bigdata/spark/roster.py` in the analytics stage). The per-row `population`
> column in the CSV/Parquet, by contrast, is the number of *members of that
> household* (a small integer) and is used by the data explorer / household
> analytics. They are different by design.

## Columns (20)

`timestamp`, `date`, `hour`, `day_of_week`, `weekday`, `month`, `year`,
`area_id`, `area_name`, `zone`, `household_id`, `building_type`, `population`,
`supplied_water_liters`, `consumed_water_liters`, `wastage_liters`,
`temperature_c`, `rainfall_mm`, `pressure_bar`, `meter_status`.

## Realism knobs baked into the generator

- **Diurnal profiles** — a 24-hour shape (% of daily volume/hour) with morning
  (06–09) and evening (18–21) peaks and a night trough.
- **Weekly** — lower consumption Mon–Thu, higher Fri–Sun (`sat` 1.10, `sun` 1.14).
- **Seasonal** — monthly factors peak in May–Jun (heat) and dip in winter.
- **Weather** — temperature drives consumption up; rainfall suppresses outdoor
  use (per-mm factor, capped at 42 mm/h).
- **Building types** — weighted mix of residential flat/house, commercial,
  industrial, institutional with different usage multipliers.
- **Meter realism** — per-meter bias, pressure noise, `ACTIVE/SUSPECT/FAULTY`
  statuses.
- **Events** — leakage windows (multi-hour, ~few/month per property) and rare
  abnormal spikes (2.2×–5×); these are what anomaly detection finds.

## Determinism

`random.Random(seed)` drives everything, so re-running with the same seed
reproduces the exact same CSV and (via the Spark pipeline) the same analytics.

## How the pipeline consumes it

1. **Ingest** — CSV read with a strict schema (typed `timestamp`, floats, etc.).
2. **Preprocess** — drop null/`¬A\d` `area_id` rows, negative consumption/supply
   fixes, `consumed ≤ supplied` sanity check.
3. **Quality report** — records read/valid/invalid, per-column nulls, duplicates.
4. **Analytics** — Spark SQL aggregations → Parquet `consumption_clean/` +
   `anomalies/`, plus 9 JSON artifacts in `bigdata/outputs/analytics/`.

## Scaling to millions (laptop-friendly)

```powershell
py -3.14 scripts/run_pipeline.py --rows 1000000          # ~1M rows
py -3.14 scripts/run_pipeline.py --households 1200 --months 12
```

| Target | Households | Rows | Approx pipeline wall time |
|---|---|---|---|
| default (350k) | 40 | 350,400 | ~4.5 min |
| 1M | ~114 | ~1.0M | ~12 min |
| 2.5M | ~285 | ~2.5M | ~30 min |
| 38M (fits laptop in minutes-scale runs) | 1,200 ± | derived | bounded by stage parallelism |

The pipeline is pure DataFrame/SQL (`local[*]`, Arrow enabled) — no `rdd`
worker paths — and writes a log + `pipeline_meta.json` with per-stage timings, so
it can be re-run at any scale: `--skip-generate` reuses an existing CSV while a
fresh `--rows` invocation regenerates it first.

### Notes

- Rows = households × months × ~30.44 days × 24 h; `--rows` only derives the
  household count (min 40, max 1,200).
- `bigdata/tmp/*.log` contain historical tensor/validation logs from development;
  they are not part of the production artifacts.