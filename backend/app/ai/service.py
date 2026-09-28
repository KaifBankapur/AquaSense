"""AquaAI orchestration — decides llm vs local mode and executes the turn."""

from __future__ import annotations

import logging

from backend.app.ai import intents
from backend.app.ai import llm as llm_client
from backend.app.core.config import get_settings

logger = logging.getLogger("aqua.ai")

SUGGESTIONS = [
    "Analyze today's water usage",
    "Find wastage hotspots",
    "Explain peak consumption",
    "Compare Hubballi Central and Vidyanagar",
    "Show anomalies",
    "Forecast next 7 days",
    "Which area wastes the most water?",
    "What percentage of supplied water is wasted?",
]


def _effective_mode() -> str:
    mode = get_settings().ai_mode
    if mode == "auto":
        return "llm" if get_settings().llm_api_key else "local"
    return mode


def answer(question: str, history: list[dict] | None = None) -> dict:
    """Handle one assistant turn.

    Returns
    -------
    dict with ``message`` (markdown), ``mode``, ``tool_calls``.
    """
    mode = _effective_mode()
    history = history or []

    if mode == "llm":
        try:
            tool_calls, message = llm_client.chat_with_llm(question, history)
            return {"message": message, "mode": "llm", "tool_calls": tool_calls}
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM path failed (%s) — falling back to local tools", exc)

    tool_calls, message, handled = intents.answer_local(question)
    return {"message": message, "mode": "local", "tool_calls": tool_calls,
            "handled": handled}


def suggestions() -> list[str]:
    return SUGGESTIONS