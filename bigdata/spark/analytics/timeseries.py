"""Spark analytics — F. Time-series aggregations.

Produces hourly / daily / weekly / monthly / yearly consumption series
with Spark groupBy + window aggregations. Output powers every trend chart
in the dashboard.
"""

from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from ..common import ANALYTICS_OUTPUT_DIR, write_json

OUT_FILE = ANALYTICS_OUTPUT_DIR / "time_series.json"


def run(spark: SparkSession, clean: DataFrame) -> dict:
    """Compute granularity-bucketed time series."""
    hour_level = (
        clean.groupBy("timestamp", "year", "month", "date", "hour")
        .agg(F.sum("consumed_water_liters").alias("consumed"),
             F.sum("wastage_liters").alias("wastage"))
        .orderBy("timestamp")
    )

    day_level = (
        clean.groupBy("date", "year", "month")
        .agg(F.sum("consumed_water_liters").alias("consumed"),
             F.sum("wastage_liters").alias("wastage"))
        .orderBy("date")
    )

    week_level = (
        clean.groupBy("year", "iso_week")
        .agg(F.min("date").alias("week_start"),
             F.sum("consumed_water_liters").alias("consumed"),
             F.sum("wastage_liters").alias("wastage"))
        .orderBy("year", "iso_week")
    )

    month_level = (
        clean.groupBy("year", "month")
        .agg(F.sum("consumed_water_liters").alias("consumed"),
             F.sum("wastage_liters").alias("wastage"))
        .orderBy("year", "month")
    )

    year_level = (
        clean.groupBy("year")
        .agg(F.sum("consumed_water_liters").alias("consumed"),
             F.sum("wastage_liters").alias("wastage"))
        .orderBy("year")
    )

    result = {
        "hourly": [
            {"timestamp": str(r["timestamp"]), "consumed": round(float(r["consumed"] or 0), 2),
             "wastage": round(float(r["wastage"] or 0), 2)}
            for r in hour_level.collect()
        ],
        "daily": [
            {"date": str(r["date"]), "consumed": round(float(r["consumed"] or 0), 2),
             "wastage": round(float(r["wastage"] or 0), 2)}
            for r in day_level.collect()
        ],
        "weekly": [
            {"week_start": str(r["week_start"]), "iso_week": int(r["iso_week"]),
             "year": int(r["year"]), "consumed": round(float(r["consumed"] or 0), 2),
             "wastage": round(float(r["wastage"] or 0), 2)}
            for r in week_level.collect()
        ],
        "monthly": [
            {"year": int(r["year"]), "month": int(r["month"]),
             "consumed": round(float(r["consumed"] or 0), 2),
             "wastage": round(float(r["wastage"] or 0), 2)}
            for r in month_level.collect()
        ],
        "yearly": [
            {"year": int(r["year"]), "consumed": round(float(r["consumed"] or 0), 2),
             "wastage": round(float(r["wastage"] or 0), 2)}
            for r in year_level.collect()
        ],
    }
    write_json(OUT_FILE, result)
    return result