"""AquaAI tool registry.

Every tool maps 1:1 to a real analytics function so the assistant can only
answer from actual data. The schemas are also handed to the LLM when
function calling is enabled.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any, Callable

from backend.app.services import analytics_service as svc

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


def _resolve_area_id(area_id: str | None = None, area_name: str | None = None) -> str | None:
    """Resolve friendly area names to area ids using real area metadata."""
    if area_id:
        return area_id
    if not area_name:
        return None
    areas = svc.get_areas()["areas"]
    norm = area_name.strip().lower()
    for a in areas:
        if norm == a["area_name"].lower():
            return a["area_id"]
    for a in areas:  # substring match
        if norm in a["area_name"].lower():
            return a["area_id"]
    return None


def tool_get_dashboard_summary() -> dict:
    return svc.get_dashboard_summary()


def tool_get_total_consumption() -> dict:
    return svc.get_summary()


def tool_get_area_consumption(area_id: str | None = None,
                              area_name: str | None = None) -> dict:
    aid = _resolve_area_id(area_id, area_name)
    if aid is None:
        return {"error": "area not found", "available": [a["area_name"] for a in svc.get_areas()["areas"]]}
    return svc.compare_areas([aid])["areas"][0]


def tool_get_area_details(area_id: str | None = None,
                          area_name: str | None = None) -> dict:
    aid = _resolve_area_id(area_id, area_name)
    if aid is None:
        return {"error": "area not found"}
    return svc.get_area_detail(aid)


def tool_get_peak_analysis() -> dict:
    return svc.get_peaks()


def tool_get_wastage_analysis() -> dict:
    return svc.get_wastage()


def tool_get_anomalies(area_ids: list[str] | None = None,
                       area_name: str | None = None,
                       severity: str | None = None,
                       limit: int = 20,
                       from_date: str | None = None,
                       to_date: str | None = None) -> dict:
    area_list = None
    if area_name:
        aid = _resolve_area_id(area_name=area_name)
        area_list = [aid] if aid else None
    if area_ids:
        area_list = area_ids
    fd = date.fromisoformat(from_date) if from_date else None
    td = date.fromisoformat(to_date) if to_date else None
    payload = svc.query_anomalies(
        area_ids=area_list, from_date=fd, to_date=td, severity=severity,
        page_size=limit)
    payload["events"] = payload["events"][:limit]
    return payload


def tool_get_forecast(horizon: str = "7d") -> dict:
    fc = svc.get_forecast()
    key = "forecast_7d" if horizon in ("7d", "7", "7 days") else "forecast_30d"
    return {"method": fc["method"], "trained_on_days": fc["trained_on_days"],
            "model_metrics": fc["model_metrics"],
            "horizon": fc[key].get("horizon_days"),
            "is_forecast": True,
            "points": fc[key]["points"],
            "disclaimer": fc["disclaimer"]}


def tool_get_daily_trend(area_id: str | None = None,
                         area_name: str | None = None,
                         from_date: str | None = None,
                         to_date: str | None = None) -> dict:
    aid = _resolve_area_id(area_id, area_name)
    fd = date.fromisoformat(from_date) if from_date else None
    td = date.fromisoformat(to_date) if to_date else None
    return svc.get_daily_trend(area_id=aid, from_date=fd, to_date=td)


def tool_get_monthly_trend(area_id: str | None = None,
                           area_name: str | None = None) -> dict:
    aid = _resolve_area_id(area_id, area_name)
    return svc.get_monthly_trend(area_id=aid)


def tool_compare_areas(area_names: list[str] | None = None,
                       area_ids: list[str] | None = None) -> dict:
    ids = area_ids or []
    if area_names:
        for name in area_names:
            aid = _resolve_area_id(area_name=name)
            if aid:
                ids.append(aid)
    ids = list(dict.fromkeys(ids))[:6]
    if not ids:
        return {"error": "no valid areas to compare",
                "available": [a["area_name"] for a in svc.get_areas()["areas"]]}
    return svc.compare_areas(ids)


def tool_get_top_consumers(limit: int = 10) -> dict:
    return svc.get_top_consumers(limit=limit)


def tool_get_data_quality() -> dict:
    return svc.get_data_quality()


# ---------------------------------------------------------------------------
# Registry + OpenAI-style schemas
# ---------------------------------------------------------------------------

Tools = dict[str, Callable[..., Any]]

TOOLS: Tools = {
    "get_dashboard_summary": tool_get_dashboard_summary,
    "get_total_consumption": tool_get_total_consumption,
    "get_area_consumption": tool_get_area_consumption,
    "get_area_details": tool_get_area_details,
    "get_peak_analysis": tool_get_peak_analysis,
    "get_wastage_analysis": tool_get_wastage_analysis,
    "get_anomalies": tool_get_anomalies,
    "get_forecast": tool_get_forecast,
    "get_daily_trend": tool_get_daily_trend,
    "get_monthly_trend": tool_get_monthly_trend,
    "compare_areas": tool_compare_areas,
    "get_top_consumers": tool_get_top_consumers,
    "get_data_quality": tool_get_data_quality,
}

SCHEMAS: list[dict] = [
    {"type": "function", "function": {"name": "get_dashboard_summary",
                                      "description": "KPI summary: totals, wastage rate, record count, active areas.",
                                      "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "get_total_consumption",
                                      "description": "Total supplied/consumed/wastage, averages, percentiles, distribution.",
                                      "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "get_area_consumption",
                                      "description": "Consumption stats for one area. Provide area_name or area_id.",
                                      "parameters": {"type": "object", "properties": {
                                          "area_name": {"type": "string"},
                                          "area_id": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "get_area_details",
                                      "description": "Deep-dive analytics for one area: trends, wastage, anomalies, forecast, comparison vs average.",
                                      "parameters": {"type": "object", "properties": {
                                          "area_name": {"type": "string"},
                                          "area_id": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "get_peak_analysis",
                                      "description": "Peak hour/day/week/month/area + 24x7 heatmap.",
                                      "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "get_wastage_analysis",
                                      "description": "Wastage totals, by-area, by-building, monthly, leak events.",
                                      "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "get_anomalies",
                                      "description": "Detected anomalies/leaks with counts, severities and event list.",
                                      "parameters": {"type": "object", "properties": {
                                          "area_name": {"type": "string"},
                                          "severity": {"type": "string"},
                                          "limit": {"type": "integer"}}}}},
    {"type": "function", "function": {"name": "get_forecast",
                                      "description": "Water demand forecast (7d/30d) with confidence intervals.",
                                      "parameters": {"type": "object", "properties": {
                                          "horizon": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "get_daily_trend",
                                      "description": "Daily consumption time series (optionally filtered by area/date).",
                                      "parameters": {"type": "object", "properties": {
                                          "area_name": {"type": "string"},
                                          "area_id": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "get_monthly_trend",
                                      "description": "Monthly consumption time series.",
                                      "parameters": {"type": "object", "properties": {
                                          "area_name": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "compare_areas",
                                      "description": "Compare consumption/wastage/average/peak between multiple areas.",
                                      "parameters": {"type": "object", "properties": {
                                          "area_names": {"type": "array", "items": {"type": "string"}}}}}},
    {"type": "function", "function": {"name": "get_top_consumers",
                                      "description": "Highest-consuming households.",
                                      "parameters": {"type": "object", "properties": {
                                          "limit": {"type": "integer"}}}}},
    {"type": "function", "function": {"name": "get_data_quality",
                                      "description": "Data quality report: valid/invalid records, duplicates, missing values.",
                                      "parameters": {"type": "object", "properties": {}}}},
]


def execute_tool(name: str, arguments: dict) -> dict:
    """Run a tool by name, tolerating unknown/malformed arguments."""
    fn = TOOLS.get(name)
    if fn is None:
        return {"error": f"unknown tool: {name}"}
    try:
        result = fn(**arguments)
        return result if isinstance(result, dict) else {"result": result}
    except TypeError as exc:
        # drop invalid args and retry — the LLM sometimes sends extra keys
        cleaned = {k: v for k, v in arguments.items()
                   if k in fn.__code__.co_varnames}
        try:
            result = fn(**cleaned)
            return result if isinstance(result, dict) else {"result": result}
        except Exception as exc2:  # noqa: BLE001
            return {"error": str(exc2), "tool": name}
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc), "tool": name}


def json_dumps(obj: Any) -> str:
    return json.dumps(obj, indent=2, default=str)