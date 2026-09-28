"""Anomalies, data explorer and CSV export routes."""

from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from backend.app.analytics.store import DatasetUnavailableError
from backend.app.services import analytics_service as svc
from backend.app.services import export_service

anomalies = APIRouter(prefix="/anomalies", tags=["anomalies"])
data = APIRouter(prefix="/data", tags=["data"])
export = APIRouter(prefix="/export", tags=["export"])


@anomalies.get("")
def list_anomalies(
    area_id: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    severity: str | None = None,
    building_type: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> dict:
    area_ids = [a.strip() for a in area_id.split(",")] if area_id else None
    bts = [b.strip() for b in building_type.split(",")] if building_type else None
    try:
        return svc.query_anomalies(
            area_ids=area_ids, from_date=from_date, to_date=to_date,
            severity=severity, building_types=bts,
            page=page, page_size=page_size)
    except DatasetUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@anomalies.get("/summary")
def anomalies_summary() -> dict:
    try:
        payload = svc.query_anomalies(page_size=100000)
        return {k: payload[k] for k in ("counts", "total_flagged",
                                        "severity_counts", "by_area")}
    except DatasetUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@data.get("")
def explore(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str | None = None,
    sort_by: str = "timestamp",
    sort_desc: bool = True,
    from_date: date | None = None,
    to_date: date | None = None,
    area_id: str | None = None,
    building_type: str | None = None,
    zone: str | None = None,
    meter_status: str | None = None,
) -> dict:
    area_ids = [a.strip() for a in area_id.split(",")] if area_id else None
    bts = [b.strip() for b in building_type.split(",")] if building_type else None
    try:
        return svc.query_rows(
            page=page, page_size=page_size, search=search,
            sort_by=sort_by, sort_desc=sort_desc,
            from_date=from_date, to_date=to_date,
            area_ids=area_ids, building_types=bts,
            zones=[zone] if zone else None)
    except DatasetUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@data.get("/columns")
def data_columns() -> dict:
    from backend.app.analytics.store import EXPLORER_COLUMNS
    return {"columns": EXPLORER_COLUMNS}


@export.get("/csv")
def export_csv(
    resource: Literal["areas", "wastage", "anomalies", "summary", "data"],
    area_id: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> StreamingResponse:
    try:
        text, filename = export_service.export_resource(
            resource, area_ids=[area_id] if area_id else None,
            from_date=from_date, to_date=to_date)
    except (DatasetUnavailableError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return StreamingResponse(
        iter([text]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"})