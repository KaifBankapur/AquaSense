"""Smart Water Consumption Analytics — FastAPI application.

Run:
    uvicorn backend.app.main:app --reload --port 8000
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.router import api
from backend.app.core.config import get_settings
from backend.app.core.database import init_db
from backend.app.core.logging import setup_logging

setup_logging()
logger = logging.getLogger("aqua")

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Big Data powered water usage, wastage and demand intelligence. "
        "PySpark → Parquet → FastAPI → React. API docs at /docs."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error",
                 "detail": "Analytics service unavailable."},
    )


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    logger.info("%s v%s started", settings.app_name, settings.app_version)
    if settings.resolved_clean_parquet.exists():
        logger.info("analytical layer found: %s", settings.resolved_clean_parquet)
    else:
        logger.warning(
            "No analytical data found. Run: python scripts/run_pipeline.py")


app.include_router(api)


@app.get("/")
def root() -> dict:
    return {
        "service": settings.app_name,
        "docs": "/docs",
        "api": "/api/health",
    }