"""Application settings (pydantic-settings).

Owner: Zhou (backend)
Feature ID: F01 (monorepo scaffold)

All secret keys are loaded here from this app's env — never the frontend.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed runtime configuration sourced from `.env` / environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str = ""
    openai_api_key: str = ""
    tavily_api_key: str = ""
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    google_solar_api_key: str = ""
    google_geocoding_api_key: str = ""
    cors_origins: list[str] = ["http://localhost:5173"]
    app_env: str = "dev"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        """Allow CORS_ORIGINS to be a comma-separated string in env."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
