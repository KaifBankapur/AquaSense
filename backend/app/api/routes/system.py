"""System routes: health checks and pipeline status."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.app.core.config import get_settings
from backend.app.schemas.common import Message
from backend.app.services import analytics_service as svc

router = APIRouter(tags=["system"])


@router.get("/health", response_model=dict)
def health() -> dict:
    settings = get_settings()
    import pyspark
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "spark": pyspark.__version__,
        "dataset_present": settings.resolved_clean_parquet.exists(),
    }


@router.get("/pipeline", response_model=dict)
def pipeline_status() -> dict:
    meta = svc.get_pipeline_meta()
    if not meta:
        raise HTTPException(
            status_code=503,
            detail="Spark pipeline has not been run yet. "
                   "Execute: python scripts/run_pipeline.py")
    return {
        **meta,
        "analytics_ready": svc._read_json_analytics("summary") is not None
        if hasattr(svc, "_read_json_analytics") else True,
    }


@router.get("/dataset/info", response_model=dict)
def dataset_info() -> dict:
    settings = get_settings()
    if not settings.generation_report.exists():
        raise HTTPException(status_code=404, detail="No dataset generated yet.")
    import json
    return json.loads(settings.generation_report.read_text(encoding="utf-8"))