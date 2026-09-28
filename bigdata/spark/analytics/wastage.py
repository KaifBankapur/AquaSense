"""Spark analytics — D. Water wastage analysis.

wastage = supplied − consumed
wastage_percentage = (wastage / supplied) × 100

Identifies highest-wastage areas/buildings, abnormal wastage periods and
leakage-like events (sustained high wastage percent).
"""

from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

from ..common import ANALYTICS_OUTPUT_DIR, write_json

OUT_FILE = ANALYTICS_OUTPUT_DIR / "wastage.json"

LEAK_PCT_THRESHOLD = 15.0  # wastage_percent that looks like a leak


def run(spark: SparkSession, clean: DataFrame) -> dict:
    """Compute wastage analytics."""
    agg = clean.agg(
        F.sum("wastage_liters").alias("total_wastage"),
        F.sum("supplied_water_liters").alias("total_supplied"),
        F.avg("wastage_percent").alias("avg_wastage_pct"),
        F.max("wastage_liters").alias("max_wastage"),
    ).collect()[0]
    total_wastage = float(agg["total_wastage"] or 0)
    total_supplied = float(agg["total_supplied"] or 0)

    # ---- by area ----------------------------------------------------------
    by_area = (
        clean.groupBy("area_id", "area_name")
        .agg(
            F.sum("wastage_liters").alias("wastage"),
            F.sum("supplied_water_liters").alias("supplied"),
            F.avg("wastage_percent").alias("avg_pct"),
        )
        .withColumn("wastage_pct",
                    F.round(F.when(F.col("supplied") > 0,
                                   F.col("wastage") / F.col("supplied") * 100).otherwise(0), 2))
        .orderBy(F.desc("wastage"))
    )

    # ---- by building type ---------------------------------------------------
    by_building = (
        clean.groupBy("building_type")
        .agg(F.sum("wastage_liters").alias("wastage"),
             F.sum("supplied_water_liters").alias("supplied"),
             F.count("*").alias("records"))
        .withColumn("wastage_pct",
                    F.round(F.when(F.col("supplied") > 0,
                                   F.col("wastage") / F.col("supplied") * 100).otherwise(0), 2))
        .orderBy(F.desc("wastage"))
    )

    # ---- abnormal wastage periods (monthly) ----------------------------------
    by_month = (
        clean.groupBy("year", "month")
        .agg(F.sum("wastage_liters").alias("wastage"),
             F.sum("supplied_water_liters").alias("supplied"))
        .withColumn("wastage_pct",
                    F.round(F.when(F.col("supplied") > 0,
                                   F.col("wastage") / F.col("supplied") * 100).otherwise(0), 2))
        .orderBy("year", "month")
    )

    # ---- leakage-like events -------------------------------------------------
    # A row is a candidate leak when its hourly wastage percent is extreme and
    # consumption itself is *not* already marked an anomaly (see anomaly stage).
    leak_candidates = clean.filter(F.col("wastage_percent") >= LEAK_PCT_THRESHOLD)
    top_leaks = (
        leak_candidates
        .select("timestamp", "area_name", "household_id", "building_type",
                "supplied_water_liters", "consumed_water_liters",
                "wastage_liters", "wastage_percent")
        .orderBy(F.desc("wastage_liters"))
        .limit(500)
    )
    leak_events = [
        {
            "timestamp": str(r["timestamp"]),
            "area_name": r["area_name"],
            "household_id": r["household_id"],
            "building_type": r["building_type"],
            "supplied_water_liters": round(float(r["supplied_water_liters"]), 1),
            "consumed_water_liters": round(float(r["consumed_water_liters"]), 1),
            "wastage_liters": round(float(r["wastage_liters"]), 1),
            "wastage_percent": round(float(r["wastage_percent"]), 2),
        }
        for r in top_leaks.collect()
    ]

    # daily wastage time-series for trend charts
    daily = (
        clean.groupBy("date")
        .agg(F.sum("wastage_liters").alias("wastage"),
             F.sum("supplied_water_liters").alias("supplied"))
        .withColumn("wastage_pct",
                    F.round(F.when(F.col("supplied") > 0,
                                   F.col("wastage") / F.col("supplied") * 100).otherwise(0), 2))
        .orderBy("date")
    )

    result = {
        "total_wastage_liters": round(total_wastage, 2),
        "total_supplied_liters": round(total_supplied, 2),
        "wastage_rate_pct": round(total_wastage / total_supplied * 100, 2) if total_supplied else 0.0,
        "avg_wastage_pct": round(float(agg["avg_wastage_pct"] or 0), 2),
        "max_wastage_single_hour": round(float(agg["max_wastage"] or 0), 2),
        "leak_threshold_pct": LEAK_PCT_THRESHOLD,
        "leak_event_count": len(leak_events),
        "by_area": [
            {"area_id": r["area_id"], "area_name": r["area_name"],
             "wastage_liters": round(float(r["wastage"] or 0), 2),
             "wastage_pct": round(float(r["wastage_pct"] or 0), 2),
             "supplied_liters": round(float(r["supplied"] or 0), 2)}
            for r in by_area.collect()
        ],
        "by_building_type": [
            {"building_type": r["building_type"],
             "wastage_liters": round(float(r["wastage"] or 0), 2),
             "wastage_pct": round(float(r["wastage_pct"] or 0), 2),
             "records": int(r["records"])}
            for r in by_building.collect()
        ],
        "monthly_wastage": [
            {"year": int(r["year"]), "month": int(r["month"]),
             "wastage_liters": round(float(r["wastage"] or 0), 2),
             "wastage_pct": round(float(r["wastage_pct"] or 0), 2)}
            for r in by_month.collect()
        ],
        "daily_wastage": [
            {"date": str(r["date"]),
             "wastage_liters": round(float(r["wastage"] or 0), 2),
             "wastage_pct": round(float(r["wastage_pct"] or 0), 2)}
            for r in daily.collect()
        ],
        "leak_events": leak_events,
    }
    write_json(OUT_FILE, result)
    return result