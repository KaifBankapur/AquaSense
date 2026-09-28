"""Analytics domain schemas (validated shapes of API responses)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from .common import AnomalyClass, Severity


# ---- dashboard -----------------------------------------------------------
class DashboardSummary(BaseModel):
    total_consumed_liters: float
    total_supplied_liters: float
    total_wastage_liters: float
    wastage_rate_pct: float
    peak_consumption_liters: float
    active_areas: int
    record_count: int
    avg_consumption: float
    generated_at: str | None = None


# ---- consumption time series ---------------------------------------------
class TrendPoint(BaseModel):
    label: str
    consumed: float
    wastage: float | None = None


class TrendResponse(BaseModel):
    granularity: str
    points: list[TrendPoint]
    filters: dict[str, Any] = {}


# ---- areas ----------------------------------------------------------------
class AreaSummary(BaseModel):
    area_id: str
    area_name: str
    zone: str
    rank: int
    total_supplied: float
    total_consumed: float
    total_wastage: float
    wastage_rate_pct: float
    efficiency_pct: float
    avg_consumption: float
    avg_household_consumption: float
    household_count: int
    population: int
    peak_hour: int
    peak_hour_liters: float


class AreaDetailResponse(BaseModel):
    area: AreaSummary
    trend_daily: list[TrendPoint]
    trend_hourly: list[TrendPoint]
    wastage_daily: list[TrendPoint]
    household_distribution: list[dict]
    anomaly_count: int
    forecast: dict[str, Any]
    comparison_vs_overall_avg: float  # % difference vs city average
    values: dict[str, Any]


# ---- wastage ----------------------------------------------------------------
class WastageResponse(BaseModel):
    total_wastage_liters: float
    wastage_rate_pct: float
    avg_wastage_pct: float
    max_wastage_single_hour: float
    leak_threshold_pct: float
    leak_event_count: int
    by_area: list[dict]
    by_building_type: list[dict]
    monthly_wastage: list[dict]
    daily_wastage: list[dict]
    leak_events: list[dict]


# ---- peaks -------------------------------------------------------------------
class PeakResponse(BaseModel):
    peak_hour: dict
    peak_day: dict
    peak_week: dict
    peak_month: dict
    peak_area: dict
    heatmap: list[dict]
    total_liters: float


# ---- anomalies -----------------------------------------------------------------
class AnomalyEvent(BaseModel):
    timestamp: datetime
    area_id: str
    area_name: str
    zone: str
    household_id: str
    building_type: str
    consumed_water_liters: float
    expected_liters: float
    deviation_pct: float
    z_score: float
    wastage_percent: float
    class_: str = Field(alias="class")
    severity: str


class AnomalyListResponse(BaseModel):
    counts: dict[str, int]
    total_flagged: int
    severity_counts: dict[str, int]
    by_area: list[dict]
    events: list[dict]
    page: int
    page_size: int
    total: int
    pages: int


# ---- forecast -------------------------------------------------------------------
class ForecastForecast(BaseModel):
    horizon_days: int
    is_forecast: bool
    points: list[dict]


class ForecastResponse(BaseModel):
    method: str
    features: list[str]
    trained_on_days: int
    history: list[dict]
    ema_history: list[float]
    model_metrics: dict[str, float]
    forecast_7d: ForecastForecast
    forecast_30d: ForecastForecast
    disclaimer: str


# ---- data explorer -----------------------------------------------------------------
class DataRowResponse(BaseModel):
    rows: list[dict]
    pagination: dict
    columns: list[str]
    filters: dict[str, Any]


# ---- quality --------------------------------------------------------------------
class QualityResponse(BaseModel):
    source: str
    total_records_read: int
    valid_records: int
    invalid_records: int
    corrupt_rows: int
    invalid_rows: int
    duplicates_removed: int
    missing_values: int
    min_consumption: float
    max_consumption: float
    avg_consumption: float
    median_consumption: float
    total_supplied: float
    total_consumed: float
    total_wastage: float
    households: int
    areas: int


# ---- assistant ---------------------------------------------------------------------
class AssistantTurn(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)
    history: list[dict] = Field(default_factory=list,
                                description="optional prior turns [{role, content}]")


class AssistantToolCall(BaseModel):
    name: str
    arguments: dict[str, Any]
    result: dict[str, Any] | None = None


class AssistantResponse(BaseModel):
    message: str
    mode: str                       # llm | local
    tool_calls: list[AssistantToolCall]
    suggestions: list[str] | None = None