"""AquaAI assistant route."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app.ai import service as ai_service
from backend.app.analytics.store import DatasetUnavailableError
from backend.app.core.config import get_settings
from backend.app.schemas.analytics import (AssistantResponse, AssistantToolCall,
                                           AssistantTurn)

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/chat", response_model=AssistantResponse)
def chat(turn: AssistantTurn) -> AssistantResponse:
    """One assistant turn. ``turn.history`` is an optional list of
    {role: user|assistant, content} messages used by the LLM path."""
    try:
        result = ai_service.answer(turn.content, turn.history)
    except DatasetUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return AssistantResponse(
        message=result["message"],
        mode=result["mode"],
        tool_calls=[AssistantToolCall(**tc) for tc in result.get("tool_calls", [])],
        suggestions=ai_service.suggestions(),
    )


@router.get("/status")
def assistant_status() -> dict:
    settings = get_settings()
    live = bool(settings.llm_api_key) and settings.ai_mode != "local"
    return {
        "name": settings.assistant_name,
        "mode": "llm" if live else "local",
        "llm_configured": bool(settings.llm_api_key),
        "provider": settings.llm_provider if live else None,
        "model": settings.llm_model if live else None,
    }