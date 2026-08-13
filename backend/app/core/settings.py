from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR.parent / ".env"


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "RedPA AI"
    app_version: str = "0.1.0"

    environment: Literal[
        "development",
        "testing",
        "staging",
        "production",
    ] = "development"

    debug: bool = True

    log_level: str = "INFO"
    log_format: str = "console"

    api_v1_prefix: str = "/api/v1"

    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)

    secret_key: str = "replace-with-a-secure-secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=30, ge=1)

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/redpa"
    )

    redis_url: str = "redis://localhost:6379/0"

    chroma_host: str = "localhost"
    chroma_port: int = Field(default=8001, ge=1, le=65535)

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"

    openai_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Return a cached application settings instance."""

    return Settings()