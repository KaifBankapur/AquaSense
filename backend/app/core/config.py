"""Application configuration (pydantic-settings, env-driven).

Never hard-code secrets in code. Copy ``.env.example`` to ``.env`` and set
values there.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Google exposes an OpenAI-compatible surface, so the assistant's function-
# calling loop serves both providers — only the base URL and model differ.
PROVIDER_BASE_URLS = {
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    "openai": "https://api.openai.com/v1",
}


class Settings(BaseSettings):
    app_name: str = "Smart Water Consumption Analytics"
    app_version: str = "1.0.0"
    api_prefix: str = "/api"

    # --- data paths -----------------------------------------------------
    # Resolved against PROJECT_ROOT when relative
    bigdata_root: Path = PROJECT_ROOT / "bigdata"
    analytics_dir: Path = PROJECT_ROOT / "bigdata" / "outputs" / "analytics"
    clean_parquet: Path = PROJECT_ROOT / "bigdata" / "data" / "processed" / "consumption_clean"
    anomaly_parquet: Path = PROJECT_ROOT / "bigdata" / "data" / "processed" / "anomalies"
    pipeline_meta: Path = PROJECT_ROOT / "bigdata" / "outputs" / "pipeline_meta.json"
    generation_report: Path = PROJECT_ROOT / "bigdata" / "data" / "raw" / "generation_report.json"

    # --- storage ----------------------------------------------------------
    database_url: str = "sqlite:///./smart_water.db"   # Postgres: postgresql+psycopg2://...
    cache_ttl_seconds: int = 300

    # --- CORS ---------------------------------------------------------------
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
    ]

    # --- AI assistant ---------------------------------------------------------
    ai_mode: str = "auto"              # auto | llm | local
    llm_provider: str = "openai"       # openai | gemini
    llm_api_key: str | None = None
    llm_base_url: str | None = None
    llm_model: str = "gpt-4o-mini"
    llm_max_tokens: int = 4096         # headroom for Gemini's internal thinking
    llm_timeout_seconds: float = 45.0
    assistant_name: str = "AquaAI"

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        env_prefix="AQUA_",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def resolved_analytics_dir(self) -> Path:
        p = Path(self.analytics_dir)
        return p if p.is_absolute() else PROJECT_ROOT / p

    @property
    def llm_endpoint(self) -> str:
        """Base URL for the configured provider, without a trailing slash.

        An explicit ``AQUA_LLM_BASE_URL`` always wins; otherwise fall back to
        the provider's known endpoint.
        """
        if self.llm_base_url:
            return self.llm_base_url.rstrip("/")
        return PROVIDER_BASE_URLS.get(
            self.llm_provider.strip().lower(), PROVIDER_BASE_URLS["openai"]
        )

    @property
    def resolved_clean_parquet(self) -> Path:
        p = Path(self.clean_parquet)
        return p if p.is_absolute() else PROJECT_ROOT / p

    @property
    def resolved_anomaly_parquet(self) -> Path:
        p = Path(self.anomaly_parquet)
        return p if p.is_absolute() else PROJECT_ROOT / p


@lru_cache
def get_settings() -> Settings:
    return Settings()