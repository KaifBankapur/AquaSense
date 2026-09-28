"""AquaAI — local (zero-LLM) assistant.

A deterministic intent router that maps natural-language questions to the
same real analytics tools the LLM would call, then renders a markdown answer
from the returned numbers. Used when no LLM API key is configured.

Every figure in the output comes from ``backend.app.services.analytics_service``;
the router never synthesises statistics.
"""

from __future__ import annotations

import re
from typing import Callable

from backend.app.ai import tools as T
from backend.app.services import analytics_service as svc

def area_names() -> list[str]:
    """Resolve available area names lazily from real analytics."""
    try:
        return [a["area_name"] for a in svc.get_areas()["areas"]]
    except Exception:  # noqa: BLE001 — analytics not ready yet
        return []


def _fmt_liters(v: float) -> str:
    return f"{v:,.0f} L" if v and v >= 1000 else f"{v:,.1f} L"


def _fmt_pct(v: float) -> str:
    return f"{v:.1f}%"


# ---------------------------------------------------------------------------
# Intent handlers — each returns (tool_calls, markdown)
# ---------------------------------------------------------------------------

def _intent_top_area(q: str) -> tuple[list[dict], str] | None:
    """'Which area consumes the most / ranks highest' questions."""
    if not re.search(r"area", q, re.IGNORECASE) or "wast" in q:
        return None
    data = svc.get_areas()
    top3 = data["areas"][:3]
    lines = ["**Area ranking by total consumption**\n",
             "| Rank | Area | Consumed | Wastage % | Avg L/h |",
             "|---|---|---|---|---|"]
    for r in top3:
        lines.append(
            f"| {r['rank']} | {r['area_name']} | {_fmt_liters(r['total_consumed'])} | "
            f"{_fmt_pct(r['wastage_rate_pct'])} | {_fmt_liters(r['avg_consumption'])} |")
    lines.append(
        f"\n**Top area:** {top3[0]['area_name']} — {_fmt_liters(top3[0]['total_consumed'])} "
        f"total consumption." if top3 else "No area data available.")
    return [{"name": "get_area_consumption", "arguments": {},
             "result": {"areas": data["areas"][:3]}}], "\n".join(lines)


def _intent_total_consumption(q: str) -> tuple[list[dict], str]:
    data = T.tool_get_total_consumption()
    a, b = f"**Total water consumption**\n\n", []
    b.append(f"- **Consumed:** {_fmt_liters(data['total_consumed_liters'])}")
    b.append(f"- **Supplied:** {_fmt_liters(data['total_supplied_liters'])}")
    b.append(f"- **Wasted:** {_fmt_liters(data['total_wastage_liters'])} "
             f"({_fmt_pct(data['wastage_rate_pct'])})")
    b.append(f"- **Average consumption / hour:** {_fmt_liters(data['avg_consumption_liters_per_hour'])}")
    b.append(f"- **Min / Median / Max:** {_fmt_liters(data['min_consumption'])} / "
             f"{_fmt_liters(data['median_consumption_liters_per_hour'])} / "
             f"{_fmt_liters(data['max_consumption'])}")
    b.append(f"- **Records analysed:** {data['record_count']:,}")
    return [{"name": "get_total_consumption", "arguments": {}, "result": data}], a + "\n".join(b)


def _intent_peak(q: str) -> tuple[list[dict], str]:
    data = T.tool_get_peak_analysis()
    lines = [
        "**Peak consumption analysis**\n",
        f"- **Peak hour:** {data['peak_hour']['label']} "
        f"({_fmt_liters(data['peak_hour']['liters'])})",
        f"- **Peak day:** {data['peak_day']['day_name']} "
        f"({_fmt_liters(data['peak_day']['liters'])})",
        f"- **Peak week:** week {data['peak_week']['week']} "
        f"({_fmt_liters(data['peak_week']['liters'])})",
        f"- **Peak month:** {data['peak_month']['year']}-{data['peak_month']['month']:02d} "
        f"({_fmt_liters(data['peak_month']['liters'])})",
        f"- **Peak area:** {data['peak_area']['area_name']} "
        f"({_fmt_liters(data['peak_area']['liters'])})",
    ]
    return [{"name": "get_peak_analysis", "arguments": {}, "result": data}], "\n".join(lines)


def _intent_wastage(q: str) -> tuple[list[dict], str]:
    data = T.tool_get_wastage_analysis()
    lines = [
        "**Water wastage analysis**\n",
        f"- **Total wastage:** {_fmt_liters(data['total_wastage_liters'])}",
        f"- **Wastage rate:** {_fmt_pct(data['wastage_rate_pct'])}",
        f"- **Avg hourly wastage %:** {_fmt_pct(data['avg_wastage_pct'])}",
        f"- **Leak-like events flagged:** {data['leak_event_count']:,}",
        "\n**Top wastage areas**\n",
    ]
    for r in data["by_area"][:5]:
        lines.append(f"- {r['area_name']}: {_fmt_liters(r['wastage_liters'])} "
                     f"({_fmt_pct(r['wastage_pct'])})")
    # monthly check for "this month" questions
    if any(w in q for w in ("this month", "monthly", "last month")):
        lines.append("\n**Monthly wastage**")
        for m in data["monthly_wastage"][-3:]:
            lines.append(f"- {m['year']}-{m['month']:02d}: "
                         f"{_fmt_liters(m['wastage_liters'])} ({_fmt_pct(m['wastage_pct'])})")
    return [{"name": "get_wastage_analysis", "arguments": {}, "result": data}], "\n".join(lines)


def _intent_forecast(q: str) -> tuple[list[dict], str]:
    horizon = "30d" if any(w in q for w in ("30", "month")) else "7d"
    data = T.tool_get_forecast(horizon=horizon)
    pts = data["points"]
    lines = [
        f"**Water demand forecast — next {data['horizon']} days**\n",
        f"Method: `{data['method']}` (trained on {data['trained_on_days']} days of "
        f"history). Forecast values are **predictions**, not measurements.\n",
    ]
    for p in pts:
        lines.append(f"- {p['date']}: **{_fmt_liters(p['predicted'])}** "
                     f"(95% CI {_fmt_liters(p['lower'])}–{_fmt_liters(p['upper'])})")
    m = data["model_metrics"]
    lines.append(f"\nModel fit — RMSE: {m['rmse']:,.1f} L, MAE: {m['mae']:,.1f} L")
    return [{"name": "get_forecast", "arguments": {"horizon": horizon}, "result": data}], "\n".join(lines)


def _intent_anomalies(q: str) -> tuple[list[dict], str]:
    data = T.tool_get_anomalies(limit=10)
    lines = [
        "**Anomaly report**\n",
        f"- **Total flagged:** {data['total_flagged']:,}",
        f"- **ANOMALY:** {data['counts'].get('ANOMALY', 0):,}",
        f"- **POSSIBLE_LEAKAGE:** {data['counts'].get('POSSIBLE_LEAKAGE', 0):,}",
        f"- **HIGH:** {data['counts'].get('HIGH', 0):,}",
        "\n**Largest anomalies**\n",
    ]
    for e in data["events"][:8]:
        cls = e.get("anomaly_class") or e.get("class") or "UNKNOWN"
        lines.append(f"- {e['timestamp']} · {e['area_name']} · {e['household_id']} "
                     f"({cls}, +{_fmt_pct(e['deviation_pct'])} vs expected)")
    return [{"name": "get_anomalies", "arguments": {"limit": 10}, "result": data}], "\n".join(lines)


def _named_area(q: str) -> str | None:
    for name in sorted(area_names(), key=len, reverse=True):
        if re.search(re.escape(name), q, re.IGNORECASE):
            return name
    return None


def _intent_area(q: str) -> tuple[list[dict], str] | None:
    name = _named_area(q)
    if not name:
        return None
    data = T.tool_get_area_details(area_name=name)
    area = data["area"]
    cmp_s = data["comparison_vs_overall_avg"]
    lines = [
        f"**{area['area_name']} — detailed analytics**\n",
        f"- **Total consumed:** {_fmt_liters(area['total_consumed'])}",
        f"- **Total wastage:** {_fmt_liters(area['total_wastage'])} "
        f"({_fmt_pct(area['wastage_rate_pct'])})",
        f"- **Average consumption / hour:** {_fmt_liters(area['avg_consumption'])} "
        f"({'above' if cmp_s > 0 else 'below'} city average by {abs(cmp_s):.1f}%)",
        f"- **Households:** {area['household_count']:,} | **Peak hour:** {area['peak_hour']:02d}:00",
        f"- **Anomalies flagged:** {data['anomaly_count']:,}",
    ]
    return [{"name": "get_area_details", "arguments": {"area_name": name}, "result": data}], "\n".join(lines)


def _intent_compare(q: str) -> tuple[list[dict], str] | None:
    names = []
    for name in sorted(area_names(), key=len, reverse=True):
        if re.search(re.escape(name), q, re.IGNORECASE):
            names.append(name)
    names = list(dict.fromkeys(names))
    if len(names) < 2:
        return None
    data = T.tool_compare_areas(area_names=names[:3])
    rows = data.get("areas", [])
    if not rows:
        return None
    header = "| Area | Consumed | Wastage | Wastage % | Avg L/h | Peak hour |"
    sep = "|---|---|---|---|---|---|"
    body = [
        f"| {r['area_name']} | {_fmt_liters(r['total_consumed'])} | "
        f"{_fmt_liters(r['total_wastage'])} | {_fmt_pct(r['wastage_rate_pct'])} | "
        f"{_fmt_liters(r['avg_consumption'])} | {r['peak_hour']:02d}:00 |"
        for r in rows
    ]
    msg = "**Area comparison**\n\n" + "\n".join([header, sep] + body)
    return [{"name": "compare_areas", "arguments": {"area_names": names[:3]}, "result": data}], msg


def _intent_trend(q: str) -> tuple[list[dict], str] | None:
    name = _named_area(q)
    wants_daily = (any(w in q for w in ("daily", "day-by-day", "per day"))
                   or re.search(r"trend|over time|history", q))
    if wants_daily:
        data = T.tool_get_daily_trend(area_name=name)
        pts = data["points"]
        lines = [f"**Daily consumption trend for {name}**" if name else "**Daily consumption trend**", *[
            f"- {p['label']}: **{_fmt_liters(p['consumed'])}**"
            + (f" (wastage {_fmt_liters(p['wastage'])})" if p.get("wastage") else "")
            for p in pts[-14:]]]
        return ([{"name": "get_daily_trend", "arguments": {"area_name": name}, "result": data}],
                "\n".join(lines))
    return None


def _intent_quality(q: str) -> tuple[list[dict], str]:
    data = T.tool_get_data_quality()
    lines = [
        "**Data quality report**\n",
        f"- **Records read:** {data['total_records_read']:,}",
        f"- **Valid records:** {data['valid_records']:,}",
        f"- **Invalid removed:** {data['invalid_records']:,} "
        f"(corrupt {data['corrupt_rows']:,}, invalid {data['invalid_rows']:,}, "
        f"duplicates {data['duplicates_removed']:,})",
        f"- **Missing values:** {data['missing_values']:,}",
        f"- **Avg consumption:** {_fmt_liters(data['avg_consumption'])}",
        f"- **Total wastage:** {_fmt_liters(data['total_wastage'])}",
    ]
    return [{"name": "get_data_quality", "arguments": {}, "result": data}], "\n".join(lines)


def _intent_top_consumers(q: str) -> tuple[list[dict], str]:
    data = T.tool_get_top_consumers(limit=8)
    lines = ["**Highest-consuming households**\n"]
    for i, r in enumerate(data["top_consumers"], 1):
        lines.append(f"{i}. {r.get('household_id')} · {r.get('area_name')} · "
                     f"{r.get('building_type')} — **{_fmt_liters(r.get('total_consumed'))}** total, "
                     f"{_fmt_liters(r.get('avg_consumption'))}/h avg")
    return [{"name": "get_top_consumers", "arguments": {"limit": 8}, "result": data}], "\n".join(lines)


def _intent_summary(q: str) -> tuple[list[dict], str]:
    data = T.tool_get_dashboard_summary()
    lines = [
        "**Dashboard summary**\n",
        f"- **Total consumed:** {_fmt_liters(data['total_consumed_liters'])}",
        f"- **Total supplied:** {_fmt_liters(data['total_supplied_liters'])}",
        f"- **Total wastage:** {_fmt_liters(data['total_wastage_liters'])} "
        f"({_fmt_pct(data['wastage_rate_pct'])})",
        f"- **Peak consumption (single hour):** {_fmt_liters(data['peak_consumption_liters'])}",
        f"- **Active areas:** {data['active_areas']} | **Records:** {data['record_count']:,}",
    ]
    return [{"name": "get_dashboard_summary", "arguments": {}, "result": data}], "\n".join(lines)


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

HANDLERS: list[tuple[re.Pattern, Callable]] = [
    (re.compile(r"which area|area (con[sz]umes?|uses)|most water|biggest area"),
     _intent_top_area),
    (re.compile(r"compare|versus|vs\.?"), _intent_compare),
    (re.compile(r"forecast|predict|next \d+ days|demand"), _intent_forecast),
    (re.compile(r"anomal|unusual|outlier|spike|suspicious"), _intent_anomalies),
    (re.compile(r"wastage|waste|leak|leakage|lost"), _intent_wastage),
    (re.compile(r"peak|busiest|highest (demand|usage) hour|when"), _intent_peak),
    (re.compile(r"top consumer|biggest (water )?user|highest consuming"), _intent_top_consumers),
    (re.compile(r"quality|valid|duplicate|clean"), _intent_quality),
    (re.compile(r"daily|trend|per day|week"), _intent_trend),
    (re.compile(r"total|consumption|supplied|how much"), _intent_total_consumption),
]


def answer_local(question: str) -> tuple[list[dict], str, bool]:
    """Route a question to analytics tools; returns (tool_calls, markdown, handled)."""
    q = question.strip().lower()

    # area-specific questions beat generic ones (e.g. trend for an area)
    if _named_area(q):
        for pat, fn in ((re.compile(r"compare|versus|vs\.?"), _intent_compare),
                        (re.compile(r"anomal|unusual"), _intent_anomalies),
                        (re.compile(r"wastage|waste|leak"), _intent_wastage),
                        (re.compile(r"trend|daily|day-by-day|consumption over"), _intent_trend)):
            if pat.search(q):
                out = fn(q)
                if out is not None:
                    return out[0], out[1], True
        out = _intent_area(q)
        if out:
            return out[0], out[1], True

    for pat, fn in HANDLERS:
        if pat.search(q):
            out = fn(q)
            if out is not None and isinstance(out[1], str):
                return out[0], out[1], True
    # fallback: dashboard summary (still data-backed)
    if any(w in q for w in ("analysis", "overview", "summary", "usage")):
        return (*_intent_summary(q), True)
    return [], (
        "I couldn't map that to an analytics question. Try asking about "
        "**peak consumption**, **wastage**, **anomalies**, **forecast**, "
        "**area analysis**, or **data quality**."
    ), False