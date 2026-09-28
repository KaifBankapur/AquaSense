"""Analytics service — reads Spark/Parquet outputs and serves the API.

This is the single source of truth that both the REST API and the AquaAI
assistant tools use, guaranteeing the assistant never invents numbers.
"""

from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from backend.app.analytics.store import (DatasetUnavailableError,
                                         build_filter, count_with_filters,
                                         groupby_pandas, table_with_filters)
from backend.app.core.config import get_settings

settings = get_settings()


# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------

class TtlJsonCache:
    """Small in-process TTL cache over the Spark JSON results."""

    def __init__(self, ttl: int) -> None:
        self._ttl = ttl
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str):
        import time
        hit = self._store.get(key)
        if hit and time.monotonic() - hit[0] < self._ttl:
            return hit[1]
        return None

    def set(self, key: str, value: Any) -> None:
        import time
        self._store[key] = (time.monotonic(), value)

    def invalidate(self) -> None:
        self._store.clear()


_cache = TtlJsonCache(settings.cache_ttl_seconds)


def _read_json_analytics(name: str) -> dict:
    cached = _cache.get(name)
    if cached is not None:
        return cached
    path = settings.resolved_analytics_dir / f"{name}.json"
    if not path.exists():
        raise DatasetUnavailableError(
            f"Analytics artifact '{name}' is missing. Run the Spark pipeline "
            "(python scripts/run_pipeline.py) and retry.")
    value = json.loads(path.read_text(encoding="utf-8"))
    _cache.set(name, value)
    return value


def load_analytics(name: str) -> dict:
    """Public loader (also used by CSV export)."""
    return _read_json_analytics(name)


# ---------------------------------------------------------------------------
# Spark-published analytics (totals / areas / peaks / wastage / forecast)
# ---------------------------------------------------------------------------

def get_summary() -> dict:
    return _read_json_analytics("summary")


def get_areas() -> dict:
    return _read_json_analytics("areas")


def get_peaks() -> dict:
    return _read_json_analytics("peaks")


def get_wastage() -> dict:
    return _read_json_analytics("wastage")


def get_forecast() -> dict:
    return _read_json_analytics("forecast")


def get_households() -> dict:
    return _read_json_analytics("households")


def get_quality() -> dict:
    return _read_json_analytics("data_quality")


def get_dashboard_summary() -> dict:
    """KPI card values, fully derived from Spark-published analytics."""
    summary = get_summary()
    areas = get_areas()
    peaks = get_peaks()
    return {
        "total_consumed_liters": summary["total_consumed_liters"],
        "total_supplied_liters": summary["total_supplied_liters"],
        "total_wastage_liters": summary["total_wastage_liters"],
        "wastage_rate_pct": summary["wastage_rate_pct"],
        "peak_consumption_liters": summary["max_consumption"],
        "active_areas": int(areas.get("count", 0)),
        "record_count": int(summary["record_count"]),
        "avg_consumption": summary["avg_consumption_liters_per_hour"],
        "peak_hour": peaks["peak_hour"]["hour"],
        "peak_area_name": peaks["peak_area"]["area_name"],
        "peak_day_name": peaks["peak_day"]["day_name"],
        "generated_at": get_pipeline_meta().get("ran_at"),
    }


# ---------------------------------------------------------------------------
# Filtered / dynamic analytics (dataframes over Parquet with pushdown)
# ---------------------------------------------------------------------------

def _filters(from_date=None, to_date=None, area_id=None, area_ids=None,
             building_type=None, zones=None) -> dict:
    area_list = [area_id] if area_id else (list(area_ids) if area_ids else None)
    bt_list = [building_type] if building_type else None
    z_list = list(zones) if zones else None
    return {"from_date": from_date, "to_date": to_date,
            "area_ids": area_list, "building_types": bt_list, "zones": z_list}


def get_daily_trend(**filters) -> dict[str, Any]:
    table = table_with_filters("clean", **_filters(**filters))
    df = table.select(["date", "consumed_water_liters", "wastage_liters"]).to_pandas()
    g = df.groupby("date").agg(
        consumed=("consumed_water_liters", "sum"),
        wastage=("wastage_liters", "sum")).reset_index()
    return {
        "granularity": "daily",
        "points": [
            {"label": str(r["date"]), "consumed": round(float(r["consumed"]), 2),
             "wastage": round(float(r["wastage"]), 2)}
            for _, r in g.iterrows()
        ],
    }


def get_hourly_trend(**filters) -> dict[str, Any]:
    table = table_with_filters("clean", **_filters(**filters))
    df = table.select(["timestamp", "consumed_water_liters",
                       "wastage_liters"]).to_pandas()
    df["hour"] = pd_dt(df["timestamp"]).dt.floor("h")
    g = df.groupby("hour").agg(consumed=("consumed_water_liters", "sum"),
                               wastage=("wastage_liters", "sum")).reset_index()
    return {
        "granularity": "hourly",
        "points": [
            {"label": str(r["hour"]), "consumed": round(float(r["consumed"]), 2),
             "wastage": round(float(r["wastage"]), 2)}
            for _, r in g.iterrows()
        ],
    }


def get_monthly_trend(**filters) -> dict[str, Any]:
    table = table_with_filters("clean", **_filters(**filters))
    df = table.select(["year", "month", "consumed_water_liters",
                       "wastage_liters"]).to_pandas()
    g = df.groupby(["year", "month"], as_index=False).agg(
        consumed=("consumed_water_liters", "sum"),
        wastage=("wastage_liters", "sum"))
    return {
        "granularity": "monthly",
        "points": [
            {"label": f"{int(r['year'])}-{int(r['month']):02d}",
             "consumed": round(float(r["consumed"]), 2),
             "wastage": round(float(r["wastage"]), 2)}
            for _, r in g.iterrows()
        ],
    }


def pd_dt(series):
    import pandas as pd
    return pd.to_datetime(series)


# ---------------------------------------------------------------------------
# Area detail & comparisons
# ---------------------------------------------------------------------------

def _area_row(area_id: str) -> dict:
    for area in get_areas()["areas"]:
        if area["area_id"] == area_id:
            return area
    raise KeyError(area_id)


def get_area_detail(area_id: str, from_date=None, to_date=None) -> dict:
    area = _area_row(area_id)
    daily = get_daily_trend(area_id=area_id, from_date=from_date, to_date=to_date)
    hourly = get_hourly_trend(area_id=area_id, from_date=from_date, to_date=to_date)
    wastage_daily = table_with_filters(
        "clean", **_filters(area_id=area_id, from_date=from_date, to_date=to_date)) \
        .select(["date", "wastage_liters"]).to_pandas()
    wg = wastage_daily.groupby("date").sum().reset_index()

    households = table_with_filters(
        "clean", **_filters(area_id=area_id, from_date=from_date, to_date=to_date)) \
        .select(["household_id", "consumed_water_liters"]).to_pandas()
    hdist = households.groupby("household_id").sum().reset_index()
    hist = histogram(hdist["consumed_water_liters"].tolist(), [0, 5e4, 1e5, 1.5e5,
                                                               2e5, 3e5, 5e5, 1e6])

    anomaly_count = count_with_filters(
        "anomaly", **{"from_date": from_date, "to_date": to_date,
                      "area_ids": [area_id]})
    forecast = get_forecast()
    overall_avg = get_summary().get("avg_consumption_liters_per_hour", 0)
    area_avg = area["avg_consumption"]
    comparison = round((area_avg - overall_avg) / overall_avg * 100, 2) \
        if overall_avg else 0.0

    values = {
        "total_consumed": area["total_consumed"],
        "total_wastage": area["total_wastage"],
        "wastage_rate_pct": area["wastage_rate_pct"],
        "avg_consumption": area_avg,
        "avg_household_consumption": area["avg_household_consumption"],
        "peak_hour": area["peak_hour"],
    }
    return {
        "area": area,
        "trend_daily": daily["points"],
        "trend_hourly": hourly["points"],
        "wastage_daily": [
            {"label": str(r["date"]), "wastage": round(float(r["wastage_liters"]), 2)}
            for _, r in wg.iterrows()],
        "household_distribution": hist,
        "anomaly_count": anomaly_count,
        "forecast": forecast,
        "comparison_vs_overall_avg": comparison,
        "values": values,
    }


def histogram(values: list[float], edges: list[float]) -> list[dict]:
    buckets = [0] * (len(edges) - 1)
    for v in values:
        for i in range(len(edges) - 1):
            if edges[i] <= v < edges[i + 1]:
                buckets[i] += 1
                break
        else:
            buckets[-1] += 1
    return [{"bucket": f"{edges[i]:,}-{edges[i+1]:,}", "count": c}
            for i, c in enumerate(buckets)]


def compare_areas(area_ids: list[str]) -> dict:
    rows = []
    for aid in area_ids[:6]:
        area = _area_row(aid)
        rows.append({
            "area_id": area["area_id"],
            "area_name": area["area_name"],
            "total_consumed": area["total_consumed"],
            "total_wastage": area["total_wastage"],
            "avg_consumption": area["avg_consumption"],
            "avg_household_consumption": area["avg_household_consumption"],
            "wastage_rate_pct": area["wastage_rate_pct"],
            "peak_hour": area["peak_hour"],
            "household_count": area["household_count"],
        })
    return {"areas": rows, "count": len(rows)}


def get_top_consumers(limit: int = 10) -> dict:
    households = get_households()
    top = households.get("top_consumers", [])[:limit]
    return {"top_consumers": top, "count": len(top)}


# ---------------------------------------------------------------------------
# Anomalies (filtered query from the anomaly Parquet layer)
# ---------------------------------------------------------------------------

def query_anomalies(area_ids: list[str] | None = None,
                    from_date=None, to_date=None,
                    severity: str | None = None,
                    building_types: list[str] | None = None,
                    anomaly_class: str | None = None,
                    page: int = 1, page_size: int = 50,
                    sort_desc: bool = True) -> dict:
    table = table_with_filters(
        "anomaly",
        **{"area_ids": area_ids, "from_date": from_date, "to_date": to_date,
           "building_types": building_types, "anomaly_class": anomaly_class})
    df = table.to_pandas()
    # Only true anomalies are "flagged"; NORMAL rows are every non-anomalous
    # reading and would inflate totals/events/counts.
    if "anomaly_class" in df.columns:
        df = df[df["anomaly_class"] != "NORMAL"]
    if severity:
        df = df[df["severity"].astype(str) == severity]

    total = len(df)
    if sort_desc:
        df = df.sort_values("deviation_pct", ascending=False)
    start = (page - 1) * page_size
    end = start + page_size
    events = df.iloc[start:end].to_dict("records")

    counts = df["anomaly_class"].value_counts().to_dict() \
        if len(df) else {}
    sev = df[df["severity"] != "none"]["severity"].value_counts().to_dict() \
        if len(df) else {}
    area_grp = df.groupby(["area_id", "area_name"]).size() \
        .reset_index(name="count").sort_values("count", ascending=False) \
        if len(df) else None

    return {
        "counts": {str(k): int(v) for k, v in counts.items()},
        "total_flagged": int(total),
        "severity_counts": {str(k): int(v) for k, v in sev.items()},
        "by_area": [json_safe(r) for r in area_grp.to_dict("records")]
        if area_grp is not None else [],
        "events": [json_safe(e) for e in events],
        "page": page, "page_size": page_size, "total": int(total),
        "pages": math.ceil(total / page_size) if total else 0,
    }


def json_safe(row: dict) -> dict:
    out = {}
    for k, v in row.items():
        if isinstance(v, (datetime,)):
            v = v.isoformat()
        elif hasattr(v, "item"):
            v = v.item()
        out[k] = v
    return out


# ---------------------------------------------------------------------------
# Data explorer (paginated)
# ---------------------------------------------------------------------------

def query_rows(page: int = 1, page_size: int = 50,
               search: str | None = None, sort_by: str = "timestamp",
               sort_desc: bool = True, **filters) -> dict:
    table = table_with_filters("clean", **filters)
    df = table.to_pandas()

    if search:
        mask = df.astype(str).apply(
            lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
        df = df[mask]

    total = len(df)
    if sort_by not in df.columns:
        sort_by = "timestamp"
    df = df.sort_values(sort_by, ascending=not sort_desc, kind="mergesort")
    start = (page - 1) * page_size
    rows = df.iloc[start:start + page_size].to_dict("records")

    return {
        "rows": [json_safe(r) for r in rows],
        "pagination": {
            "page": page, "page_size": page_size, "total": int(total),
            "pages": math.ceil(total / page_size) if total else 0,
        },
        "columns": EXPLORER_COLUMNS,
        "filters": {k: v for k, v in filters.items() if v is not None},
    }


from backend.app.analytics.store import EXPLORER_COLUMNS  # noqa: E402


# ---------------------------------------------------------------------------
# Pipeline metadata
# ---------------------------------------------------------------------------

def get_pipeline_meta() -> dict:
    path: Path = settings.pipeline_meta
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def get_data_quality() -> dict:
    return get_quality()


def clear_cache() -> None:
    _cache.invalidate()