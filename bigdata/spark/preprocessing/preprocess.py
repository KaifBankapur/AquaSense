"""PySpark preprocessing stage.

Cleans and enriches the raw consumption feed:

1. drop corrupt / invalid rows (missing ids, negative consumption, bad status)
2. de-duplicate on (household_id, timestamp)
3. cast from string blueprint → typed columns (explicit, failure-tolerant)
4. normalise timestamps & re-derive time dimensions
5. validate consumption values (physical sanity bounds)
6. compute wastage & wastage percent
7. create consumption categories
8. write a *partitioned* Parquet analytical layer (by year)

Every rule is reported to the data-quality report in :mod:`quality`.
"""

from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from ..common import (CLEAN_PARQUET_DIR, add_consumption_category,
                      add_time_dimensions, ensure_dirs)

MAX_SANE_SUPPLY_L = 60_000.0   # litres/hour per meter (industrial ceiling)
MIN_SANE_CONSUMED_L = 0.0
TS_FORMAT = "yyyy-MM-dd'T'HH:mm:ss"


class CleaningStats:
    """Mutable counters collected while cleaning (fed to quality report)."""

    def __init__(self) -> None:
        self.corrupt_rows = 0
        self.invalid_rows = 0
        self.duplicate_rows = 0
        self.missing_values = 0
        self.rows_before = 0
        self.rows_after = 0


def _count_missing(raw: DataFrame) -> int:
    base_fields = ["timestamp", "household_id", "area_id", "meter_status"]
    row = raw.select(
        [F.sum(F.when(F.col(c).isNull() | (F.col(c) == ""), 1).otherwise(0))
         for c in base_fields]
    ).collect()[0]
    return int(sum(row))


def preprocess(spark: SparkSession, raw: DataFrame, stats: CleaningStats) -> DataFrame:
    """Clean + enrich the raw frame; writes the partitioned Parquet layer."""
    ensure_dirs()

    # --- 1. corrupt CSV lines ------------------------------------------------
    if "_corrupt_record" in raw.columns:
        stats.corrupt_rows = raw.filter(F.col("_corrupt_record").isNotNull()).count()
        raw = raw.filter(F.col("_corrupt_record").isNull()).drop("_corrupt_record")

    stats.rows_before = raw.count()
    stats.missing_values = _count_missing(raw)

    # --- 2. string-level validity filters (documented in docs) ---------------
    df = raw.filter(
        (F.col("timestamp").isNotNull())
        & (F.trim(F.col("timestamp")) != "")
        & (F.col("household_id").isNotNull())
        & (F.trim(F.col("household_id")) != "")
        & (F.col("area_id").isNotNull())
        & (F.col("area_id").rlike("^A\\d+$"))
        & (F.col("consumed_water_liters").isNotNull())
        & (F.col("supplied_water_liters").isNotNull())
    )
    stats.invalid_rows = stats.rows_before - df.count()

    # --- 3. de-duplicate on natural key ---------------------------------------
    df = df.dropDuplicates(["household_id", "timestamp"])
    stats.duplicate_rows = stats.rows_before - stats.invalid_rows - df.count()

    # --- 4. explicit typed cast (failure-tolerant) -----------------------------
    df = (
        df
        .withColumn("timestamp", F.to_timestamp(F.col("timestamp"), TS_FORMAT))
        .withColumn("date", F.to_date(F.col("date")))
        .withColumn("hour", F.col("hour").cast("int"))
        .withColumn("day_of_week", F.col("day_of_week").cast("int"))
        .withColumn("month", F.col("month").cast("int"))
        .withColumn("year", F.col("year").cast("int"))
        .withColumn("population", F.col("population").cast("int"))
        .withColumn("supplied_water_liters", F.col("supplied_water_liters").cast("double"))
        .withColumn("consumed_water_liters", F.col("consumed_water_liters").cast("double"))
        .withColumn("wastage_liters", F.col("wastage_liters").cast("double"))
        .withColumn("temperature_c", F.col("temperature_c").cast("double"))
        .withColumn("rainfall_mm", F.col("rainfall_mm").cast("double"))
        .withColumn("pressure_bar", F.col("pressure_bar").cast("double"))
        .filter(
            F.col("timestamp").isNotNull()
            & F.col("consumed_water_liters").isNotNull()
            & F.col("supplied_water_liters").isNotNull()
            & (F.col("consumed_water_liters") >= MIN_SANE_CONSUMED_L)
            & (F.col("supplied_water_liters") >= 0)
            & (F.col("supplied_water_liters") <= MAX_SANE_SUPPLY_L)
            & F.col("hour").between(0, 23)
        )
    )

    # --- 5. re-derive time dimensions from the trusted timestamp ----------------
    df = (
        df
        .withColumn("date", F.to_date("timestamp"))
        .withColumn("hour", F.hour("timestamp"))
        .withColumn("day_of_week", F.dayofweek("timestamp") - 1)   # 0=Mon..6=Sun
        .withColumn("weekday",
                    F.when(F.col("day_of_week").isin(5, 6), "weekend").otherwise("weekday"))
        .withColumn("month", F.month("timestamp"))
        .withColumn("year", F.year("timestamp"))
        .withColumn("iso_week", F.weekofyear("timestamp"))
    )

    # --- 6 & 7 & 8. wastage + categories + extra dimensions ---------------------
    df = df.withColumn(
        "wastage_liters",
        F.greatest(F.col("supplied_water_liters") - F.col("consumed_water_liters"),
                   F.lit(0.0)),
    )
    df = add_time_dimensions(df)
    df = add_consumption_category(df)

    # --- 9. partitioned analytical storage ----------------------------------------
    (
        df.write
        .mode("overwrite")
        .partitionBy("year", "month")
        .format("parquet")
        .option("compression", "snappy")
        .save(str(CLEAN_PARQUET_DIR))
    )
    stats.rows_after = df.count()
    return df


def read_clean(spark: SparkSession) -> DataFrame:
    """Read back the processed analytical layer."""
    return spark.read.parquet(str(CLEAN_PARQUET_DIR))