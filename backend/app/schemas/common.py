"""Shared API schemas (pagination, date ranges, filters)."""

from __future__ import annotations

from datetime import date as date_type
from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["critical", "high", "medium", "low", "none"]
AnomalyClass = Literal["NORMAL", "HIGH", "ANOMALY", "POSSIBLE_LEAKAGE"]


class DateRange(BaseModel):
    from_date: date_type | None = None
    to_date: date_type | None = None


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    pages: int


class ErrorResponse(BaseModel):
    error: str
    detail: str


class Kpi(BaseModel):
    key: str
    label: str
    value: float | int
    unit: str
    icon: str | None = None
    sparkline: list[float] | None = None


class Message(BaseModel):
    message: str