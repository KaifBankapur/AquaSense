"""AquaAI — optional LLM integration (OpenAI-compatible function calling).

Only used when ``AQUA_LLM_API_KEY`` is configured. The LLM decides which
analytics tools to call; every number the assistant reports comes from the
tool results.

Supports both OpenAI and Google Gemini: Gemini is reached through Google's
OpenAI-compatible endpoint, so the same tool loop serves either provider.
"""

from __future__ import annotations

import json
import logging

from backend.app.ai.tools import SCHEMAS, execute_tool
from backend.app.core.config import get_settings

logger = logging.getLogger("aqua.ai.llm")

SYSTEM_PROMPT = (
    "You are AquaAI, a water-consumption analytics assistant inside the "
    "Smart Water Consumption Analytics platform — a Big Data project. "
    "You answer questions using ONLY the analytics tools provided. "
    "Never invent statistics: if a number is not present in a tool result, "
    "do not report it. Prefer concise markdown, tables for comparisons, and "
    "always state clearly when a value is a forecast/prediction."
)


def chat_with_llm(question: str, history: list[dict]) -> tuple[list[dict], str]:
    """Run one LLM turn with function calling. Returns (tool_calls, answer)."""
    from openai import OpenAI

    settings = get_settings()
    if not settings.llm_api_key:
        raise RuntimeError("LLM not configured (AQUA_LLM_API_KEY missing).")

    client = OpenAI(api_key=settings.llm_api_key,
                    base_url=settings.llm_endpoint,
                    timeout=settings.llm_timeout_seconds)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history[-8:])
    messages.append({"role": "user", "content": question})

    tool_calls: list[dict] = []
    for _ in range(6):  # bounded tool loop
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            tools=SCHEMAS,
            tool_choice="auto",
            # Gemini 2.5 spends part of this budget on internal reasoning
            # before emitting the answer; without headroom the reply gets
            # truncated mid-word.
            max_tokens=settings.llm_max_tokens,
        )
        msg = response.choices[0].message
        if msg.tool_calls:
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                result = execute_tool(tc.function.name, args)
                tool_calls.append({"name": tc.function.name,
                                   "arguments": args,
                                   "result": result})
                messages.append({
                    "role": "assistant",
                    "tool_calls": [tc.model_dump()],
                    "content": None,
                })
                messages.append({"role": "tool",
                                 "tool_call_id": tc.id,
                                 "content": json.dumps(result, default=str)})
            continue
        return tool_calls, msg.content or ""

    return tool_calls, ("I could not finish the analysis within the allowed "
                        "number of tool calls. Try rephrasing the question.")