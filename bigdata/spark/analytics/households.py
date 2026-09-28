"""Spark analytics — E. Household / property-level analysis.

Highest/lowest consumers, average household consumption, consumption
distribution and unusual behaviour detection (coefficient of variation).
"""

from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from ..common import ANALYTICS_OUTPUT_DIR, write_json

OUT_FILE = ANALYTICS_OUTPUT_DIR / "households.json"


def run(spark: SparkSession, clean: DataFrame) -> dict:
    """Compute per-household analytics."""
    per_household = (
        clean.groupBy("household_id", "area_id", "area_name", "building_type", "zone")
        .agg(
            F.count("*").alias("record_count"),
            F.sum("consumed_water_liters").alias("total_consumed"),
            F.avg("consumed_water_liters").alias("avg_consumption"),
            F.stddev("consumed_water_liters").alias("stddev_consumption"),
            F.sum("wastage_liters").alias("total_wastage"),
            F.avg("wastage_percent").alias("avg_wastage_pct"),
        )
        .withColumn(
            "cv",
            F.when(F.col("avg_consumption") > 0,
                   F.col("stddev_consumption") / F.col("avg_consumption")).otherwise(0.0),
        )
    )

    top = per_household.orderBy(F.desc("total_consumed")).limit(25)
    bottom = (
        per_household.filter(F.col("total_consumed") > 0)
        .orderBy(F.asc("total_consumed")).limit(25)
    )

    # unusual behaviour: very high coefficient of variation AND high volume
    unusual = (
        per_household
        .filter((F.col("cv") > 0.9) & (F.col("total_consumed") > 0))
        .orderBy(F.desc("cv"))
        .limit(100)
    )

    # consumption distribution buckets (average hourly litres)
    distribution = (
        per_household
        .withColumn("bucket", F.when(F.col("avg_consumption") < 25, "0-25")
                    .when(F.col("avg_consumption") < 50, "25-50")
                    .when(F.col("avg_consumption") < 100, "50-100")
                    .when(F.col("avg_consumption") < 200, "100-200")
                    .when(F.col("avg_consumption") < 400, "200-400")
                    .otherwise("400+"))
        .groupBy("bucket")
        .agg(F.count("*").alias("households"),
             F.avg("avg_consumption").alias("avg_liters"))
        .orderBy("bucket")
    )

    summary = per_household.agg(
        F.count("*").alias("households"),
        F.avg("avg_consumption").alias("avg_household_consumption"),
        F.avg("total_consumed").alias("avg_household_total"),
        F.avg("avg_wastage_pct").alias("avg_wastage_pct"),
    ).collect()[0]

    def _rows(df, keys):
        return [{k: r[k] for k in keys} for r in df.collect()]

    result = {
        "household_count": int(summary["households"]),
        "avg_household_hourly_liters": round(float(summary["avg_household_consumption"] or 0), 2),
        "avg_household_total_liters": round(float(summary["avg_household_total"] or 0), 2),
        "avg_wastage_pct": round(float(summary["avg_wastage_pct"] or 0), 2),
        "top_consumers": _rows(
            top, ["household_id", "area_name", "building_type", "zone",
                  "total_consumed", "avg_consumption", "avg_wastage_pct"]),
        "lowest_consumers": _rows(
            bottom, ["household_id", "area_name", "building_type", "zone",
                     "total_consumed", "avg_consumption", "avg_wastage_pct"]),
        "unusual_households": _rows(
            unusual, ["household_id", "area_name", "building_type",
                      "cv", "total_consumed", "avg_consumption"]),
        "distribution": [
            {"bucket": r["bucket"], "households": int(r["households"]),
             "avg_liters": round(float(r["avg_liters"] or 0), 2)}
            for r in distribution.collect()
        ],
    }
    # normalise floats for JSON-safety
    for group in ("top_consumers", "lowest_consumers", "unusual_households"):
        for item in result[group]:
            for k in ("total_consumed", "avg_consumption", "avg_wastage_pct", "cv"):
                if k in item:
                    item[k] = round(float(item[k] or 0), 2)

    write_json(OUT_FILE, result)
    return result