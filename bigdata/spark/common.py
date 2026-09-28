"""Smart Water Analytics — shared Spark pipeline helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DATA_DIR = PROJECT_ROOT / "bigdata" / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "bigdata" / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "bigdata" / "outputs"
ANALYTICS_OUTPUT_DIR = OUTPUT_DIR / "analytics"

RAW_CSV_PATH = RAW_DATA_DIR / "consumption_hourly.csv"
CLEAN_PARQUET_DIR = PROCESSED_DATA_DIR / "consumption_clean"
ANOMALY_PARQUET_DIR = PROCESSED_DATA_DIR / "anomalies"
FORECAST_PARQUET_DIR = PROCESSED_DATA_DIR / "forecast"
AREA_META_FILE = RAW_DATA_DIR / "meta_areas.json"

# Column sets -------------------------------------------------------------

RAW_SCHEMA_DDL = """
    timestamp TIMESTAMP,
    date DATE,
    hour INT,
    day_of_week INT,
    weekday STRING,
    month INT,
    year INT,
    area_id STRING,
    area_name STRING,
    zone STRING,
    household_id STRING,
    building_type STRING,
    population INT,
    supplied_water_liters DOUBLE,
    consumed_water_liters DOUBLE,
    wastage_liters DOUBLE,
    temperature_c DOUBLE,
    rainfall_mm DOUBLE,
    pressure_bar DOUBLE,
    meter_status STRING
"""

CATEGORY_BUCKETS = [0, 5, 10, 20, 40, 75, 125, 200]
CATEGORY_LABELS = [
    "very_low", "low", "moderate_low", "moderate", "moderate_high",
    "high", "very_high", "extreme",
]


def ensure_dirs() -> None:
    for d in (RAW_DATA_DIR, PROCESSED_DATA_DIR, OUTPUT_DIR,
              ANALYTICS_OUTPUT_DIR, FORECAST_PARQUET_DIR):
        d.mkdir(parents=True, exist_ok=True)


def write_json(target: Path, payload: Any) -> Path:
    """Atomically persist an analytics result as JSON."""
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    tmp.replace(target)
    return target


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def add_time_dimensions(df: DataFrame) -> DataFrame:
    """Add analyst-friendly time columns (hour of day, week, iso day)."""
    return (
        df
        .withColumn("hour_of_day", F.hour("timestamp"))
        .withColumn("iso_week", F.weekofyear("timestamp"))
        .withColumn("day_of_week_name", F.date_format("timestamp", "EEE"))
        .withColumn("is_weekend", F.when(F.col("day_of_week").isin(5, 6), 1).otherwise(0))
        .withColumn("wastage_percent", F.round(
            F.when(F.col("supplied_water_liters") > 0,
                   F.col("wastage_liters") / F.col("supplied_water_liters") * 100.0)
            .otherwise(0.0), 2))
    )


def add_consumption_category(df: DataFrame) -> DataFrame:
    """Bucket each row into a consumption category (L/hour)."""
    whens = None
    for i, (lo, hi) in enumerate(zip(CATEGORY_BUCKETS[:-1], CATEGORY_BUCKETS[1:])):
        cond = (F.col("consumed_water_liters") >= lo) & (F.col("consumed_water_liters") < hi)
        whens = cond if whens is None else (whens | cond)
    expr = F.when(F.col("consumed_water_liters") >= CATEGORY_BUCKETS[-1], "extreme")
    for i in range(len(CATEGORY_BUCKETS) - 2, -1, -1):
        lo = CATEGORY_BUCKETS[i]
        expr = expr.when((F.col("consumed_water_liters") >= lo)
                         & (F.col("consumed_water_liters") < CATEGORY_BUCKETS[i + 1]),
                         CATEGORY_LABELS[i])
    return df.withColumn("consumption_category", expr.otherwise("unknown"))


def sql(spark: SparkSession) -> None:
    """Central storage of a view name is unnecessary; query engines differ."""


def load_area_meta(spark: SparkSession) -> DataFrame:
    """Read the synthetic area roster (produced by scripts/generate_dataset.py)."""
    meta = read_json(AREA_META_FILE)
    return spark.createDataFrame(meta["areas"])


def to_records(df: DataFrame, limit: int | None = None) -> list[dict]:
    """Collect a DataFrame into Python dicts (JVM-side conversion, JSON-safe)."""
    rows = df.collect()
    out = [row.asDict() for row in rows]
    if limit is not None:
        out = out[:limit]
    return out