"""Data-quality report generation (Spark aggregation → JSON).

Computes a verifiable quality snapshot that the FastAPI surface exposes
under ``GET /api/data-quality``.
"""

from __future__ import annotations

from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from ..preprocessing.preprocess import CleaningStats  # noqa: F401  (re-export)
from ..common import ANALYTICS_OUTPUT_DIR, write_json

QUALITY_REPORT_FILE = ANALYTICS_OUTPUT_DIR / "data_quality.json"


def build_quality_report(spark: SparkSession, clean: DataFrame,
                         stats: "CleaningStats") -> dict:
    """Compute descriptive quality statistics over the cleaned layer."""
    if clean.select(F.lit(1)).limit(1).count() == 0:
        raise RuntimeError("Refusing to write a quality report over empty data.")

    agg = clean.agg(
        F.count("*").alias("valid_records"),
        F.sum("supplied_water_liters").alias("total_supplied"),
        F.sum("consumed_water_liters").alias("total_consumed"),
        F.sum("wastage_liters").alias("total_wastage"),
        F.min("consumed_water_liters").alias("min_consumption"),
        F.max("consumed_water_liters").alias("max_consumption"),
        F.avg("consumed_water_liters").alias("avg_consumption"),
        F.approx_count_distinct("household_id").alias("households"),
        F.approx_count_distinct("area_id").alias("areas"),
    ).collect()[0]

    median = clean.approxQuantile("consumed_water_liters", [0.5], 0.01)[0]

    report = {
        "source": "pyspark-preprocess",
        "total_records_read": stats.rows_before,
        "valid_records": int(agg["valid_records"]),
        "invalid_records": stats.corrupt_rows + stats.invalid_rows + stats.duplicate_rows,
        "corrupt_rows": stats.corrupt_rows,
        "invalid_rows": stats.invalid_rows,
        "duplicates_removed": stats.duplicate_rows,
        "missing_values": stats.missing_values,
        "min_consumption": round(float(agg["min_consumption"] or 0), 2),
        "max_consumption": round(float(agg["max_consumption"] or 0), 2),
        "avg_consumption": round(float(agg["avg_consumption"] or 0), 2),
        "median_consumption": round(float(median), 2),
        "total_supplied": round(float(agg["total_supplied"] or 0), 2),
        "total_consumed": round(float(agg["total_consumed"] or 0), 2),
        "total_wastage": round(float(agg["total_wastage"] or 0), 2),
        "households": int(agg["households"]),
        "areas": int(agg["areas"]),
    }
    write_json(QUALITY_REPORT_FILE, report)
    return report