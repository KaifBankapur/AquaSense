"""Big Data ingestion stage.

Reads the raw CSV as a *string-typed* DataFrame (schema-on-read) so that no
data is silently coerced to NULL during ingestion. Malformed lines are
captured into ``_corrupt_record`` and counted in the quality report. Type
coercion happens afterwards in the preprocessing stage where corruption can
be handled explicitly.

Demonstrates:

* lazy schema-on-read (Spark infers nothing — we declare a string blueprint)
* PERMISSIVE mode + corrupt-record capture
* partitioning hints for downstream stages
"""

from __future__ import annotations

from pyspark.sql import SparkSession, DataFrame

from ..common import RAW_CSV_PATH, ensure_dirs

STRING_SCHEMA_DDL = """
    timestamp STRING,
    date STRING,
    hour STRING,
    day_of_week STRING,
    weekday STRING,
    month STRING,
    year STRING,
    area_id STRING,
    area_name STRING,
    zone STRING,
    household_id STRING,
    building_type STRING,
    population STRING,
    supplied_water_liters STRING,
    consumed_water_liters STRING,
    wastage_liters STRING,
    temperature_c STRING,
    rainfall_mm STRING,
    pressure_bar STRING,
    meter_status STRING
"""


def load_raw(spark: SparkSession, path: str | None = None) -> DataFrame:
    """Load the raw CSV with a string blueprint; capture malformed lines."""
    ensure_dirs()
    csv_path = str(path or RAW_CSV_PATH)
    return (
        spark.read
        .option("header", "true")
        .option("mode", "PERMISSIVE")               # don't crash on bad lines
        .option("columnNameOfCorruptRecord", "_corrupt_record")
        .schema(STRING_SCHEMA_DDL)
        .csv(csv_path)
    )