"""Wastage, peaks, forecast and quality routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app.analytics.store import DatasetUnavailableError
from backend.app.services import analytics_service as svc

wastage = APIRouter(prefix="/wastage", tags=["wastage"])
peaks = APIRouter(prefix="/peak", tags=["peaks"])
forecast = APIRouter(prefix="/forecast", tags=["forecast"])
quality = APIRouter(prefix="/data-quality", tags=["quality"])


def _guard(fn):
    try:
        return fn()
    except DatasetUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@wastage.get("")
def wastage_overview() -> dict:
    return _guard(svc.get_wastage)


@wastage.get("/areas")
def wastage_by_area() -> dict:
    data = _guard(svc.get_wastage)
    return {"areas": data["by_area"], "count": len(data["by_area"])}


@wastage.get("/leaks")
def wastage_leaks() -> dict:
    data = _guard(svc.get_wastage)
    return {"leak_events": data["leak_events"],
            "leak_event_count": data["leak_event_count"],
            "threshold_pct": data["leak_threshold_pct"]}


@peaks.get("")
def peak_overview() -> dict:
    return _guard(svc.get_peaks)


@forecast.get("")
def forecast_overview() -> dict:
    return _guard(svc.get_forecast)


@quality.get("")
def quality_overview() -> dict:
    return _guard(svc.get_quality)


@quality.get("/report")
def quality_report() -> dict:
    return _guard(svc.get_quality)