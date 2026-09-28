"""PyArrow-backed Parquet store.

The Spark pipeline writes a *partitioned, columnar* analytical layer; this
store reads it with predicate pushdown and exposes filtered views for the
API — we never load the whole dataset into memory when a filter can be
pushed into Parquet row groups.

For huge datasets the recommended production serving layer is a Presto /
Trino or DuckDB/Athena store in front of the same Parquet; this module keeps
the laptop demo honest and fast.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Iterable

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.parquet as pq

from backend.app.core.config import get_settings

settings = get_settings()

# columns exposed to the API (whitelist prevents injection)
EXPLORER_COLUMNS = [
    "timestamp", "date", "hour", "day_of_week", "weekday", "month", "year",
    "area_id", "area_name", "zone", "household_id", "building_type",
    "population", "supplied_water_liters", "consumed_water_liters",
    "wastage_liters", "wastage_percent", "temperature_c", "rainfall_mm",
    "pressure_bar", "meter_status", "consumption_category",
]

ANOMALY_COLUMNS = ["timestamp", "area_id", "area_name", "zone", "household_id",
                   "building_type", "consumed_water_liters", "rolling_mean",
                   "rolling_std", "deviation_pct", "z_score", "wastage_percent",
                   "anomaly_class", "severity"]


class DatasetUnavailableError(RuntimeError):
    """Raised when the processed analytical layer is missing."""


def _dataset(path) -> ds.Dataset:
    try:
        return ds.dataset(str(path), format="parquet",
                          partitioning=ds.partitioning(
                              pa.schema([("year", pa.int32()), ("month", pa.int32())]),
                              flavor="hive"))
    except (FileNotFoundError, pa.ArrowInvalid) as exc:  # pragma: no cover
        raise DatasetUnavailableError(
            "No analytical data available. Run the Spark pipeline first:\n"
            "  python scripts/run_pipeline.py") from exc


def date_ok(d: date | None) -> bool:
    return d is not None


def build_filter(from_date: date | None = None, to_date: date | None = None,
                 area_ids: Iterable[str] | None = None,
                 building_types: Iterable[str] | None = None,
                 zones: Iterable[str] | None = None,
                 anomaly_class: str | None = None) -> pc.Expression | None:
    """Compose an Arrow filter expression from API query parameters."""
    exprs: list[pc.Expression] = []
    if from_date is not None:
        exprs.append(pc.field("date") >= pc.scalar(from_date))
    if to_date is not None:
        exprs.append(pc.field("date") <= pc.scalar(to_date))
    if area_ids:
        exprs.append(pc.field("area_id").isin(list(area_ids)))
    if building_types:
        exprs.append(pc.field("building_type").isin(list(building_types)))
    if zones:
        exprs.append(pc.field("zone").isin(list(zones)))
    if anomaly_class:
        exprs.append(pc.field("anomaly_class") == anomaly_class)
    if not exprs:
        return None
    result = exprs[0]
    for e in exprs[1:]:
        result = result & e
    return result


def ensure_layer_exists() -> None:
    clean = settings.resolved_clean_parquet
    if not clean.exists():
        raise DatasetUnavailableError(
            "No analytical data available — the Spark pipeline has not been "
            "run on this machine yet.")
    anom = settings.resolved_anomaly_parquet
    if not anom.exists():
        raise DatasetUnavailableError(
            "Anomaly layer missing — re-run the Spark pipeline "
            "(anomaly.detection stage).")


def table_with_filters(kind: str = "clean", **filters) -> pa.Table:
    """Return a filtered (but unsorted, unlimited) table from a parquet layer."""
    ensure_layer_exists()
    if kind == "clean":
        ds_obj = _dataset(settings.resolved_clean_parquet)
        cols = EXPLORER_COLUMNS
    elif kind == "anomaly":
        ds_obj = _dataset(settings.resolved_anomaly_parquet)
        cols = ANOMALY_COLUMNS
    else:
        raise ValueError(f"unknown layer: {kind}")

    expr = build_filter(**filters)
    if expr is not None:
        return ds_obj.to_table(columns=cols, filter=expr)
    return ds_obj.to_table(columns=cols)


def count_with_filters(kind: str = "clean", **filters) -> int:
    ensure_layer_exists()
    if kind == "clean":
        ds_obj = _dataset(settings.resolved_clean_parquet)
    elif kind == "anomaly":
        ds_obj = _dataset(settings.resolved_anomaly_parquet)
    else:
        raise ValueError(f"unknown layer: {kind}")
    expr = build_filter(**filters)
    if expr is None:
        return int(ds_obj.count_rows())
    table = ds_obj.to_table(columns=["household_id"], filter=expr)
    return table.num_rows


def groupby_pandas(table: pa.Table, keys: list[str],
                   agg: dict[str, str]) -> "pandas.DataFrame":
    """Group the table with pandas on top of an Arrow pushdown read."""
    import pandas as pd  # local import keeps Spark-side bootstrap lean
    df = table.to_pandas()
    return df.groupby(keys, as_index=False).agg(agg)