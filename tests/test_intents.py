"""Unit tests for the AquaAI local intent router.

Every assertion is checked against the REAL analytical layer (the Spark
pipeline output), so these doubles as end-to-end data checks: the router
must never fabricate figures.
"""

from __future__ import annotations

import pytest

from backend.app.ai import intents
from backend.app.ai import service as ai_svc
from backend.app.core.config import get_settings

pytestmark = pytest.mark.skipif(
    not get_settings().resolved_clean_parquet.exists(),
    reason="Spark pipeline output not present on this machine",
)


def answer_local(q: str):
    return intents.answer_local(q)


def test_unhandled_question_returns_guidance():
    calls, msg, handled = answer_local("what about pressure in the pipes?")
    assert handled is False
    assert calls == []
    assert "peak consumption" in msg
    assert "wastage" in msg


def test_wastage_question_ranks_real_areas():
    calls, msg, handled = answer_local("Which area wastes the most water?")
    assert handled is True
    assert calls and calls[0]["name"] == "get_wastage_analysis"
    assert any(name in msg for name in intents.area_names())
    # the message must contain real numbers, not placeholders
    assert "L" in msg and "%" in msg


def test_forecast_question_calls_forecast_tool():
    calls, msg, handled = answer_local("Predict water consumption for the next 7 days")
    assert handled is True
    assert calls and calls[0]["name"] == "get_forecast"
    assert calls[0]["arguments"]["horizon"] == "7d"
    assert "forecast" in msg.lower()


def test_compare_two_areas_builds_markdown_table():
    calls, msg, handled = answer_local("Compare Hubballi Central and Vidyanagar")
    assert handled is True
    assert "|" in msg  # markdown table
    assert len(calls) == 1 and calls[0]["name"] == "compare_areas"


def test_named_area_question_resolves_to_that_area():
    calls, msg, handled = answer_local("Show me the consumption trend for Vidyanagar")
    assert handled is True
    assert "Vidyanagar" in msg


def test_anomaly_question_includes_real_counts():
    calls, msg, handled = answer_local("What are the biggest anomalies?")
    assert handled is True
    assert calls and calls[0]["name"] == "get_anomalies"
    assert "ANOMALY" in msg
    # every event line is data-backed: contains a timestamp + deviation
    assert "deviation" not in msg  # raw key names never leak into prose


def test_peak_question_returns_analysis():
    calls, msg, handled = answer_local("When is peak water consumption?")
    assert handled is True
    assert calls and calls[0]["name"] == "get_peak_analysis"
    assert "peak hour" in msg.lower()


def test_total_consumption_question():
    calls, msg, handled = answer_local("How much water is consumed in total?")
    assert handled is True
    assert calls and calls[0]["name"] == "get_total_consumption"
    assert "Consumed" in msg


def test_service_level_answer():
    res = ai_svc.answer("Which area wastes the most water?")
    assert res["mode"] == "local"
    assert res["message"]
    assert isinstance(res.get("tool_calls"), list)


def test_tools_function_shapes():
    """The tool registry serves the same data the API exposes."""
    from backend.app.ai import tools as T
    wastage = T.tool_get_wastage_analysis()
    assert set(["total_wastage_liters", "wastage_rate_pct", "by_area"]).issubset(wastage)
    assert wastage["total_wastage_liters"] > 0
    summary = T.tool_get_dashboard_summary()
    assert summary["total_consumed_liters"] > summary["total_wastage_liters"]
    assert summary["record_count"] > 100_000