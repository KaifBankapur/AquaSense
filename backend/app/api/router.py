"""API router aggregation."""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.api.routes import (areas, assistant, dashboard, explore,
                                    insights, system)

api = APIRouter(prefix="/api")

api.include_router(system.router)          # /api/health, /api/pipeline ...
api.include_router(dashboard.router)       # /api/dashboard/*
api.include_router(areas.router)           # /api/areas/*
api.include_router(insights.wastage)       # /api/wastage/*
api.include_router(insights.peaks)         # /api/peak
api.include_router(insights.forecast)      # /api/forecast
api.include_router(insights.quality)       # /api/data-quality
api.include_router(explore.anomalies)      # /api/anomalies/*
api.include_router(explore.data)           # /api/data
api.include_router(explore.export)         # /api/export/csv
api.include_router(assistant.router)       # /api/assistant/*