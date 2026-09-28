"""Spark analytics — A. Total consumption summary."""

from __future__ import annotations

import math

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from ..common import ANALYTICS_OUTPUT_DIR, write_json

OUT_FILE = ANALYTICS_OUTPUT_DIR / "summary.json"


def run(spark: SparkSession, clean: DataFrame) -> dict:
    """Compute totals: supplied / consumed / wastage / avg / median / min / max."""
    agg = clean.agg(
        F.sum("supplied_water_liters").alias("total_supplied"),
        F.sum("consumed_water_liters").alias("total_consumed"),
        F.sum("wastage_liters").alias("total_wastage"),
        F.avg("consumed_water_liters").alias("avg_consumption"),
        F.min("consumed_water_liters").alias("min_consumption"),
        F.max("consumed_water_liters").alias("max_consumption"),
        F.avg("wastage_percent").alias("avg_wastage_pct"),
    ).collect()[0]

    median = clean.approxQuantile("consumed_water_liters", [0.5], 0.01)[0]
    quartiles = clean.approxQuantile("consumed_water_liters", [0.25, 0.75], 0.01)
    p95 = clean.approxQuantile("consumed_water_liters", [0.95], 0.01)[0]

    total_supplied = float(agg["total_supplied"] or 0)
    total_consumed = float(agg["total_consumed"] or 0)
    total_wastage = float(agg["total_wastage"] or 0)

    summary = {
        "total_supplied_liters": round(total_supplied, 2),
        "total_consumed_liters": round(total_consumed, 2),
        "total_wastage_liters": round(total_wastage, 2),
        "wastage_rate_pct": round(total_wastage / total_supplied * 100, 2)
        if total_supplied else 0.0,
        "avg_consumption_liters_per_hour": round(float(agg["avg_consumption"] or 0), 2),
        "median_consumption_liters_per_hour": round(float(median), 2),
        "p25": round(float(quartiles[0]), 2),
        "p75": round(float(quartiles[1]), 2),
        "p95": round(float(p95), 2),
        "min_consumption": round(float(agg["min_consumption"] or 0), 2),
        "max_consumption": round(float(agg["max_consumption"] or 0), 2),
        "stddev_consumption": round(
            float(clean.select(F.stddev("consumed_water_liters")).collect()[0][0] or 0), 2),
        "record_count": clean.count(),
        "approx_pi": None,  # placeholder removed in production build
    }
    summary.pop("approx_pi", None)

    # distribution histogram over consumption categories
    dist = (
        clean.groupBy("consumption_category")
        .agg(F.count("*").alias("records"), F.sum("consumed_water_liters").alias("liters"))
        .orderBy("consumption_category")
    )
    summary["distribution"] = [
        {"category": r["consumption_category"], "records": int(r["records"]),
         "liters": round(float(r["liters"] or 0), 2)}
        for r in dist.collect()
    ]
    write_json(OUT_FILE, summary)
    return summary