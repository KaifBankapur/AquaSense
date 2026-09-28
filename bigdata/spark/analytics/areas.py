"""Spark analytics — B. Area-wise analysis & ranking.

Per-area aggregates: consumption, supply, wastage, efficiency, household
count, per-household average, plus the dominant peak hour per area.
"""

from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

from ..common import ANALYTICS_OUTPUT_DIR, write_json
from ..roster import AREA_ROSTER

OUT_FILE = ANALYTICS_OUTPUT_DIR / "areas.json"


def run(spark: SparkSession, clean: DataFrame) -> dict:
    """Compute area-wise analytics, ranked by consumption."""
    areas = (
        clean.groupBy("area_id", "area_name", "zone")
        .agg(
            F.sum("supplied_water_liters").alias("total_supplied"),
            F.sum("consumed_water_liters").alias("total_consumed"),
            F.sum("wastage_liters").alias("total_wastage"),
            F.avg("consumed_water_liters").alias("avg_consumption"),
            F.avg("wastage_percent").alias("avg_wastage_pct"),
            F.countDistinct("household_id").alias("household_count"),
        )
        .withColumn(
            "wastage_rate_pct",
            F.round(F.when(F.col("total_supplied") > 0,
                           F.col("total_wastage") / F.col("total_supplied") * 100)
                    .otherwise(0), 2),
        )
        .withColumn(
            "efficiency_pct",
            F.round(F.when(F.col("total_supplied") > 0,
                           F.col("total_consumed") / F.col("total_supplied") * 100)
                    .otherwise(0), 2),
        )
        .withColumn(
            "avg_household_consumption",
            F.round(F.col("total_consumed") / F.when(F.col("household_count") > 0,
                                                     F.col("household_count")).otherwise(1), 2),
        )
    )

    # rank by total consumption
    rank_win = Window.orderBy(F.desc("total_consumed"))
    areas_ranked = areas.withColumn("rank", F.row_number().over(rank_win))

    # dominant peak hour per area
    hourly = (
        clean.groupBy("area_id", "hour")
        .agg(F.sum("consumed_water_liters").alias("liters"))
    )
    peak_win = Window.partitionBy("area_id").orderBy(F.desc("liters"))
    peak_hours = (
        hourly.withColumn("rn", F.row_number().over(peak_win))
        .filter(F.col("rn") == 1)
        .select("area_id", F.col("hour").alias("peak_hour"),
                F.col("liters").alias("peak_hour_liters"))
    )

    joined = areas_ranked.join(peak_hours, "area_id", "left").orderBy("rank")

    records = []
    for r in joined.collect():
        records.append({
            "area_id": r["area_id"],
            "area_name": r["area_name"],
            "zone": r["zone"],
            "rank": int(r["rank"]),
            "total_supplied": round(float(r["total_supplied"] or 0), 2),
            "total_consumed": round(float(r["total_consumed"] or 0), 2),
            "total_wastage": round(float(r["total_wastage"] or 0), 2),
            "wastage_rate_pct": round(float(r["wastage_rate_pct"] or 0), 2),
            "efficiency_pct": round(float(r["efficiency_pct"] or 0), 2),
            "avg_consumption": round(float(r["avg_consumption"] or 0), 2),
            "avg_household_consumption": round(float(r["avg_household_consumption"] or 0), 2),
            "household_count": int(r["household_count"]),
            "population": int(AREA_ROSTER.get(r["area_id"], {}).get("population", 0) or 0),
            "peak_hour": int(r["peak_hour"] if r["peak_hour"] is not None else -1),
            "peak_hour_liters": round(float(r["peak_hour_liters"] or 0), 2),
        })

    write_json(OUT_FILE, {"areas": records, "count": len(records)})
    return {"areas": records, "count": len(records)}