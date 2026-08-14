from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(
        default="RedPA AI",
        alias="APP_NAME",
    )

    app_version: str = Field(
        default="8.0.0",
        alias="APP_VERSION",
    )

    environment: str = Field(
        default="development",
        alias="ENVIRONMENT",
    )

    debug: bool = Field(
        default=True,
        alias="DEBUG",
    )

    api_v1_prefix: str = Field(
        default="/api/v1",
        alias="API_V1_PREFIX",
    )

    database_url: str = Field(
        alias="DATABASE_URL",
    )

    jwt_secret_key: str = Field(
        alias="JWT_SECRET_KEY",
    )

    jwt_algorithm: str = Field(
        default="HS256",
        alias="JWT_ALGORITHM",
    )

    access_token_expire_minutes: int = Field(
        default=30,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )

    cors_allowed_origins: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://128.0.0.1:3000",
            "http://localhost:5173",
            "http://128.0.0.1:5173",
        ],
        alias="CORS_ALLOWED_ORIGINS",
    )

    ollama_base_url: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_BASE_URL",
    )

    ollama_model: str = Field(
        default="qwen2.5:7b",
        alias="OLLAMA_MODEL",
    )

    ollama_timeout_seconds: float = Field(
        default=120.0,
        alias="OLLAMA_TIMEOUT_SECONDS",
    )

    ollama_temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
        alias="OLLAMA_TEMPERATURE",
    )

    ollama_max_context_messages: int = Field(
        default=20,
        ge=1,
        le=100,
        alias="OLLAMA_MAX_CONTEXT_MESSAGES",
    )

    @field_validator(
        "cors_allowed_origins",
        mode="before",
    )
    @classmethod
    def parse_cors_allowed_origins(
        cls,
        value: str | list[str],
    ) -> list[str]:
        if isinstance(value, list):
            return value

        if isinstance(value, str):
            cleaned_value = value.strip()

            if not cleaned_value:
                return []

            if cleaned_value.startswith("["):
                import json

                return json.loads(cleaned_value)

            return [
                origin.strip()
                for origin in cleaned_value.split(",")
                if origin.strip()
            ]

        raise ValueError(
            "CORS_ALLOWED_ORIGINS must be a list or comma-separated string."
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()