"""Spark analytics — C. Peak consumption analysis.

Finds the peak hour / day / week / month / area and produces the
Hour × Day-of-week heatmap used by the Peak Analysis page.
"""

from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from ..common import ANALYTICS_OUTPUT_DIR, write_json

OUT_FILE = ANALYTICS_OUTPUT_DIR / "peaks.json"

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def run(spark: SparkSession, clean: DataFrame) -> dict:
    """Compute peak consumption facts + 7×24 intensity matrix."""
    totals = clean.select(F.sum("consumed_water_liters").alias("t")).collect()[0]["t"] or 1.0

    # ---- peak hour -------------------------------------------------------
    peak_hour = (
        clean.groupBy("hour").agg(F.sum("consumed_water_liters").alias("liters"))
        .orderBy(F.desc("liters")).first()
    )
    # ---- peak day (of week) ----------------------------------------------
    peak_dow = (
        clean.groupBy("day_of_week").agg(F.sum("consumed_water_liters").alias("liters"))
        .orderBy(F.desc("liters")).first()
    )
    # ---- peak week --------------------------------------------------------
    peak_week = (
        clean.groupBy("iso_week")
        .agg(F.min("timestamp").alias("week_start"),
             F.sum("consumed_water_liters").alias("liters"))
        .orderBy(F.desc("liters")).first()
    )
    # ---- peak month -------------------------------------------------------
    peak_month = (
        clean.groupBy("year", "month").agg(F.sum("consumed_water_liters").alias("liters"))
        .orderBy(F.desc("liters")).first()
    )
    # ---- peak area --------------------------------------------------------
    peak_area = (
        clean.groupBy("area_id", "area_name")
        .agg(F.sum("consumed_water_liters").alias("liters"))
        .orderBy(F.desc("liters")).first()
    )

    # ---- heatmap: day_of_week × hour --------------------------------------
    heat = (
        clean.groupBy("day_of_week", "hour")
        .agg(F.sum("consumed_water_liters").alias("liters"))
        .collect()
    )
    grid = {}
    for r in heat:
        dow, hr = int(r["day_of_week"]), int(r["hour"])
        grid.setdefault(dow, {})[hr] = round(float(r["liters"] or 0), 2)

    heatmap = []
    for dow in range(7):
        for hr in range(24):
            v = grid.get(dow, {}).get(hr, 0.0)
            heatmap.append({
                "day_of_week": dow,
                "day_name": DAY_NAMES[dow],
                "hour": hr,
                "liters": v,
                "share_pct": round(v / totals * 100, 4),
            })

    result = {
        "peak_hour": {
            "hour": int(peak_hour["hour"]),
            "liters": round(float(peak_hour["liters"]), 2),
            "label": f"{peak_hour['hour']:02d}:00",
        },
        "peak_day": {
            "day": int(peak_dow["day_of_week"]),
            "day_name": DAY_NAMES[int(peak_dow["day_of_week"])],
            "liters": round(float(peak_dow["liters"]), 2),
        },
        "peak_week": {
            "week": int(peak_week["iso_week"]),
            "week_start": str(peak_week["week_start"])[:10],
            "liters": round(float(peak_week["liters"]), 2),
        },
        "peak_month": {
            "year": int(peak_month["year"]),
            "month": int(peak_month["month"]),
            "liters": round(float(peak_month["liters"]), 2),
        },
        "peak_area": {
            "area_id": peak_area["area_id"],
            "area_name": peak_area["area_name"],
            "liters": round(float(peak_area["liters"]), 2),
        },
        "heatmap": heatmap,
        "total_liters": round(float(totals), 2),
    }
    write_json(OUT_FILE, result)
    return result