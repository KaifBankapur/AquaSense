"""Spark anomaly detection — G.

Method: rolling window z-score.

For every (household, hour) we compute a rolling 7-day (168 h) mean and
standard deviation of *consumed* litres per household using a Spark SQL
window partitioned by ``household_id`` and ordered by ``timestamp``.

    z = (consumed − rolling_mean) / rolling_std

Labels:

    NORMAL             |z| < 2
    HIGH               2 ≤ z < 3        (elevated usage, watch)
    ANOMALY            z ≥ 3            (statistical outlier — spike/event)
    POSSIBLE_LEAKAGE   wastage % ≥ 15%  (supply ≫ consumption while usage
                                          itself is not anomalous)

Severity is derived from z-score / wastage magnitude so the UI can sort
by impact. The algorithm is documented in docs/anomaly-detection notes
inside docs/project-report.md.
"""

from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

from ..common import (ANALYTICS_OUTPUT_DIR, ANOMALY_PARQUET_DIR, write_json)

OUT_FILE = ANALYTICS_OUTPUT_DIR / "anomalies.json"
Z_HIGH = 2.0
Z_ANOMALY = 3.0
LEAK_PCT = 15.0
ROLLING_HOURS = 7 * 24


def run(spark: SparkSession, clean: DataFrame) -> dict:
    """Label anomalies, persist labeled layer + a queryable events JSON."""
    # Rolling stats per household (168h look-back, inclusive current row)
    win = (
        Window.partitionBy("household_id")
        .orderBy("timestamp")
        .rowsBetween(-ROLLING_HOURS + 1, 0)
    )

    labeled = (
        clean
        .withColumn("rolling_mean", F.avg("consumed_water_liters").over(win))
        .withColumn("rolling_std", F.stddev("consumed_water_liters").over(win))
        .withColumn(
            "z_score",
            F.when(F.col("rolling_std") > 0,
                   (F.col("consumed_water_liters") - F.col("rolling_mean"))
                   / F.col("rolling_std"))
            .otherwise(0.0),
        )
        .withColumn(
            "deviation_pct",
            F.round(
                F.when(F.col("rolling_mean") > 0,
                       (F.col("consumed_water_liters") - F.col("rolling_mean"))
                       / F.col("rolling_mean") * 100.0)
                .otherwise(0.0), 2),
        )
        .withColumn(
            "anomaly_class",
            F.when(F.col("wastage_percent") >= LEAK_PCT, "POSSIBLE_LEAKAGE")
            .when(F.col("z_score") >= Z_ANOMALY, "ANOMALY")
            .when(F.col("z_score") >= Z_HIGH, "HIGH")
            .otherwise("NORMAL"),
        )
        .withColumn(
            "severity",
            F.when(F.col("anomaly_class") == "ANOMALY",
                   F.when(F.col("z_score") >= 5, "critical").otherwise("high"))
            .when(F.col("anomaly_class") == "POSSIBLE_LEAKAGE",
                  F.when(F.col("wastage_percent") >= 30, "critical").otherwise("high"))
            .when(F.col("anomaly_class") == "HIGH", "medium")
            .otherwise("none"),
        )
    )

    # persist labeled layer (partitioned by year for scalable reads)
    (
        labeled.write
        .mode("overwrite")
        .partitionBy("year")
        .format("parquet")
        .option("compression", "snappy")
        .save(str(ANOMALY_PARQUET_DIR))
    )

    counts = (
        labeled.groupBy("anomaly_class")
        .agg(F.count("*").alias("count"))
        .collect()
    )
    count_map = {r["anomaly_class"]: int(r["count"]) for r in counts}

    severity_counts = (
        labeled.filter(F.col("severity") != "none")
        .groupBy("severity").agg(F.count("*").alias("count"))
        .collect()
    )

    # --- event list (anomalies + leaks only) -------------------------------
    events = (
        labeled.filter(F.col("anomaly_class") != "NORMAL")
        .select("timestamp", "area_id", "area_name", "zone", "household_id",
                "building_type", "consumed_water_liters", "rolling_mean",
                "rolling_std", "deviation_pct", "z_score", "wastage_percent",
                "anomaly_class", "severity")
        .orderBy(
            F.when(F.col("severity") == "critical", 0)
            .when(F.col("severity") == "high", 1)
            .otherwise(2),
            F.desc("deviation_pct"),
        )
        .limit(5000)
    )

    event_rows = [
        {
            "timestamp": str(r["timestamp"]),
            "area_id": r["area_id"],
            "area_name": r["area_name"],
            "zone": r["zone"],
            "household_id": r["household_id"],
            "building_type": r["building_type"],
            "consumed_water_liters": round(float(r["consumed_water_liters"] or 0), 2),
            "expected_liters": round(float(r["rolling_mean"] or 0), 2),
            "deviation_pct": round(float(r["deviation_pct"] or 0), 2),
            "z_score": round(float(r["z_score"] or 0), 2),
            "wastage_percent": round(float(r["wastage_percent"] or 0), 2),
            "class": r["anomaly_class"],
            "severity": r["severity"],
        }
        for r in events.collect()
    ]

    # anomaly timeline (daily counts) for the timeline chart
    timeline = (
        labeled.filter(F.col("anomaly_class") != "NORMAL")
        .groupBy("date", "anomaly_class")
        .agg(F.count("*").alias("count"))
        .orderBy("date")
    )

    # per area counts
    by_area = (
        labeled.filter(F.col("anomaly_class") != "NORMAL")
        .groupBy("area_id", "area_name")
        .agg(F.count("*").alias("count"))
        .orderBy(F.desc("count"))
    )

    result = {
        "method": "rolling_zscore",
        "rolling_hours": ROLLING_HOURS,
        "z_high": Z_HIGH,
        "z_anomaly": Z_ANOMALY,
        "leak_pct_threshold": LEAK_PCT,
        "counts": count_map,
        "total_flagged": sum(v for k, v in count_map.items() if k != "NORMAL"),
        "severity_counts": {r["severity"]: int(r["count"]) for r in severity_counts},
        "timeline": [
            {"date": str(r["date"]), "class": r["anomaly_class"], "count": int(r["count"])}
            for r in timeline.collect()
        ],
        "by_area": [
            {"area_id": r["area_id"], "area_name": r["area_name"], "count": int(r["count"])}
            for r in by_area.collect()
        ],
        "events": event_rows,
        "labels": ["NORMAL", "HIGH", "ANOMALY", "POSSIBLE_LEAKAGE"],
    }
    write_json(OUT_FILE, result)
    return result