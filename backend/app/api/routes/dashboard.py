"""Dashboard routes: summary KPIs + consumption trends."""

from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from backend.app.analytics.store import DatasetUnavailableError
from backend.app.schemas.common import Message
from backend.app.services import analytics_service as svc

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary() -> dict:
    try:
        return svc.get_dashboard_summary()
    except DatasetUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/trend")
def trend(
    granularity: Literal["hourly", "daily", "weekly", "monthly", "yearly"] = "daily",
    from_date: date | None = None,
    to_date: date | None = None,
    area_id: str | None = None,
    building_type: str | None = None,
) -> dict:
    try:
        if granularity == "daily":
            return svc.get_daily_trend(from_date=from_date, to_date=to_date,
                                       area_id=area_id, building_type=building_type)
        if granularity == "monthly":
            return svc.get_monthly_trend(area_id=area_id)
        if granularity == "hourly":
            return svc.get_hourly_trend(from_date=from_date, to_date=to_date,
                                        area_id=area_id,
                                        building_type=building_type)
        # weekly / yearly come from the Spark-published time_series
        ts = svc.load_analytics("time_series")
        points = ts.get(("weekly" if granularity == "weekly" else "yearly"), [])
        return {"granularity": granularity, "points": points}
    except DatasetUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/kpis")
def kpis() -> list[dict]:
    """KPI cards with real sparkline data (no fabricated deltas)."""
    try:
        summary = svc.get_dashboard_summary()
        daily = svc.get_daily_trend()["points"]
        series = [p["consumed"] for p in daily[-30:]]
        return [
            {"key": "total_consumption", "label": "Total Consumption",
             "value": summary["total_consumed_liters"], "unit": "liters",
             "icon": "droplets", "sparkline": series[-30:]},
            {"key": "total_supplied", "label": "Total Water Supplied",
             "value": summary["total_supplied_liters"], "unit": "liters",
             "icon": "water", "sparkline": series[-30:]},
            {"key": "total_wastage", "label": "Total Wastage",
             "value": summary["total_wastage_liters"], "unit": "liters",
             "icon": "alert-triangle", "sparkline": None},
            {"key": "wastage_rate", "label": "Wastage Rate",
             "value": summary["wastage_rate_pct"], "unit": "%",
             "icon": "percent", "sparkline": None},
            {"key": "peak_consumption", "label": "Peak Consumption",
             "value": summary["peak_consumption_liters"], "unit": "L / hour",
             "icon": "activity", "sparkline": None},
            {"key": "active_areas", "label": "Active Areas",
             "value": summary["active_areas"], "unit": "areas",
             "icon": "map-pin", "sparkline": None},
        ]
    except DatasetUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/health")
def dashboard_health() -> Message:
    return Message(message="dashboard ok")