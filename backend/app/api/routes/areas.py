"""Area analytics routes: list, detail, comparison."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query

from backend.app.analytics.store import DatasetUnavailableError
from backend.app.services import analytics_service as svc

router = APIRouter(prefix="/areas", tags=["areas"])


@router.get("")
def list_areas() -> dict:
    try:
        return svc.get_areas()
    except DatasetUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/compare")
def compare(area_ids: str = Query(..., description="comma-separated area ids")) -> dict:
    ids = [a.strip() for a in area_ids.split(",") if a.strip()]
    try:
        return svc.compare_areas(ids)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"area not found: {exc}") from exc


@router.get("/top-consumers")
def top_consumers(limit: int = Query(10, ge=1, le=100)) -> dict:
    try:
        return svc.get_top_consumers(limit=limit)
    except DatasetUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/{area_id}")
def area_detail(area_id: str,
                from_date: date | None = None,
                to_date: date | None = None) -> dict:
    try:
        return svc.get_area_detail(area_id, from_date=from_date, to_date=to_date)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"area not found: {exc}") from exc
    except DatasetUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc