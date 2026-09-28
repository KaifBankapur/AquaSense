"""API contract tests — every endpoint returns real, well-shaped analytics.

These run through the FastAPI TestClient and hit the actual Parquet
analytical layer produced by the Spark pipeline, so they also serve as a
smoke check that the whole stack is wired end to end.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.main import app

pytestmark = pytest.mark.skipif(
    not get_settings().resolved_clean_parquet.exists(),
    reason="Spark pipeline output not present on this machine",
)

client = TestClient(app)

AREAS_URL = "/api/areas"


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["dataset_present"] is True
    assert body["spark"]  # real PySpark version string


def test_pipeline_meta():
    r = client.get("/api/pipeline")
    assert r.status_code == 200
    meta = r.json()
    assert meta["analytics_ready"] is True
    assert int(meta["processed_records"]) > 100_000
    assert meta["outputs"]["analytics_files"]


def test_dashboard_summary_shapes():
    r = client.get("/api/dashboard/summary")
    assert r.status_code == 200
    s = r.json()
    assert s["total_consumed_liters"] > 0
    assert s["total_supplied_liters"] >= s["total_consumed_liters"]
    assert 0 <= s["wastage_rate_pct"] < 100
    assert s["active_areas"] >= 10
    assert s["record_count"] > 100_000


def test_kpis_are_six_cards_with_real_values():
    r = client.get("/api/dashboard/kpis")
    assert r.status_code == 200
    cards = r.json()
    assert len(cards) == 6
    keys = {c["key"] for c in cards}
    assert {"total_consumption", "total_supplied", "total_wastage",
            "wastage_rate", "peak_consumption", "active_areas"} <= keys


def test_trend_daily_and_hourly():
    daily = client.get("/api/dashboard/trend", params={"granularity": "daily"})
    assert daily.status_code == 200
    assert daily.json()["points"]
    hourly = client.get("/api/dashboard/trend", params={"granularity": "hourly"})
    assert hourly.status_code == 200
    # one point per hour across the whole dataset
    assert len(hourly.json()["points"]) >= 24


def test_areas_and_comparison():
    r = client.get(AREAS_URL)
    assert r.status_code == 200
    areas = r.json()["areas"]
    assert len(areas) >= 10
    ids = [a["area_id"] for a in areas[:2]]
    cmp = client.get(AREAS_URL + "/compare", params={"area_ids": ",".join(ids)})
    assert cmp.status_code == 200
    assert len(cmp.json()["areas"]) == 2


def test_area_detail_roundtrip():
    area = client.get(AREAS_URL).json()["areas"][0]
    r = client.get(f"{AREAS_URL}/{area['area_id']}")
    assert r.status_code == 200
    detail = r.json()
    assert detail["area"]["area_name"] == area["area_name"]
    assert detail["trend_daily"] and detail["anomaly_count"] >= 0
    assert detail["forecast"]["method"]


def test_wastage_and_leaks():
    r = client.get("/api/wastage")
    assert r.status_code == 200
    w = r.json()
    assert w["total_wastage_liters"] > 0
    assert w["by_area"] and len(w["by_area"]) >= 10
    leaks = client.get("/api/wastage/leaks")
    assert leaks.status_code == 200
    assert leaks.json()["leak_event_count"] > 0


def test_peak_analysis():
    r = client.get("/api/peak")
    assert r.status_code == 200
    p = r.json()
    assert "peak_hour" in p
    assert p["peak_hour"]["hour"] == 19  # deterministic dataset peak
    assert p["peak_hour"]["liters"] > 0


def test_forecast_artifact():
    r = client.get("/api/forecast")
    assert r.status_code == 200
    f = r.json()
    assert f["method"].startswith("seasonal_linear_regression")
    assert len(f["forecast_7d"]["points"]) == 7
    assert len(f["forecast_30d"]["points"]) == 30
    assert f["model_metrics"]["rmse"] > 0


def test_anomalies_summary_is_flagged_only():
    r = client.get("/api/anomalies/summary")
    assert r.status_code == 200
    s = r.json()
    assert s["total_flagged"] > 0
    # NORMAL must never inflate the flagged totals
    assert "NORMAL" not in s.get("counts", {})
    assert len(s["by_area"]) > 0
    assert s["total_flagged"] == s["counts"].get("ANOMALY", 0) \
        + s["counts"].get("POSSIBLE_LEAKAGE", 0) \
        + s["counts"].get("HIGH", 0)


def test_anomalies_pagination():
    r = client.get("/api/anomalies", params={"page": 1, "page_size": 25})
    assert r.status_code == 200
    body = r.json()
    assert len(body["events"]) <= 25
    assert body["total"] == body["total_flagged"]
    assert all(e["anomaly_class"] != "NORMAL" for e in body["events"])


def test_data_explorer_paginated_and_searchable():
    r = client.get("/api/data", params={"page": 1, "page_size": 10})
    assert r.status_code == 200
    body = r.json()
    assert body["rows"] and len(body["rows"]) == 10
    assert body["pagination"]["total"] > 100_000
    cols = client.get("/api/data/columns").json()["columns"]
    assert "consumed_water_liters" in cols


def test_data_quality_report():
    r = client.get("/api/data-quality")
    assert r.status_code == 200
    q = r.json()
    assert q["total_records_read"] == q["valid_records"] + q["invalid_records"]
    assert q["valid_records"] > 100_000


def test_assistant_status_and_chat():
    status = client.get("/api/assistant/status")
    assert status.status_code == 200
    body = status.json()
    assert body["name"] == "AquaAI"
    assert body["mode"] in ("llm", "local")

    r = client.post("/api/assistant/chat", json={"content": "Which area wastes the most water?"})
    assert r.status_code == 200
    chat = r.json()
    assert chat["mode"] in ("llm", "local")
    assert chat["message"]
    assert any(tc["name"] == "get_wastage_analysis" for tc in chat["tool_calls"])
    assert len(chat["suggestions"]) >= 4


def test_export_csv_endpoint():
    r = client.get("/api/export/csv", params={"resource": "areas"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert "area_name" in r.text
    rows = r.text.strip().splitlines()
    assert len(rows) == 11  # header + 10 areas