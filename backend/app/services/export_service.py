"""Comma-separated-value export for analytical results.

Exports are generated on the backend from real analytics so they always
match what the dashboard shows.
"""

from __future__ import annotations

import csv
import io
from typing import Any

from backend.app.analytics.store import EXPLORER_COLUMNS, table_with_filters
from backend.app.services import analytics_service as svc


def _rows_to_csv(rows: list[dict], columns: list[str]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({c: row.get(c, "") for c in columns})
    return buf.getvalue()


def export_resource(resource: str, **filters) -> tuple[str, str]:
    """Return (csv_text, filename) for a requested resource."""
    if resource == "areas":
        payload = svc.get_areas()["areas"]
        columns = ["rank", "area_name", "zone", "total_supplied", "total_consumed",
                   "total_wastage", "wastage_rate_pct", "efficiency_pct",
                   "avg_consumption", "avg_household_consumption",
                   "household_count", "population", "peak_hour"]
        return _rows_to_csv(payload, columns), "areas.csv"

    if resource == "wastage":
        payload = svc.get_wastage()
        return _rows_to_csv(payload.get("by_area", []),
                            ["area_name", "supplied_liters", "wastage_liters",
                             "wastage_pct"]), "wastage_by_area.csv"

    if resource == "anomalies":
        payload = svc.query_anomalies(page_size=5000)
        return _rows_to_csv(payload.get("events", []),
                            ["timestamp", "area_name", "household_id",
                             "building_type", "consumed_water_liters",
                             "expected_liters", "deviation_pct", "z_score",
                             "class", "severity"]), "anomalies.csv"

    if resource == "summary":
        s = svc.get_summary()
        rows = [{"metric": k, "value": v} for k, v in s.items()
                if not isinstance(v, list)]
        return _rows_to_csv(rows, ["metric", "value"]), "summary.csv"

    if resource == "data":
        payload = svc.query_rows(page=1, page_size=100000, **filters)
        rows = payload.get("rows", [])
        cols = [c for c in EXPLORER_COLUMNS if c in (rows[0] if rows else {})]
        if not cols:
            cols = EXPLORER_COLUMNS[:12]
        return _rows_to_csv(rows, cols), "consumption_data.csv"

    raise ValueError(f"Unknown export resource: {resource}")


def export_areas_csv() -> tuple[str, str]:
    return export_resource("areas")


def export_wastage_csv() -> tuple[str, str]:
    return export_resource("wastage")


def export_anomalies_csv() -> tuple[str, str]:
    return export_resource("anomalies")


def export_summary_csv() -> tuple[str, str]:
    return export_resource("summary")