from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.
    """

    # Application
    app_name: str = "RedPA AI"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True

    # API
    api_v1_prefix: str = "/api/v1"

    # Server
    host: str = "127.0.0.1"
    port: int = 8000

    # Logging
    log_level: str = "INFO"

    # CORS
    cors_allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    cors_allowed_methods: list[str] = [
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ]

    cors_allowed_headers: list[str] = ["*"]

    cors_exposed_headers: list[str] = [
        "X-Request-ID",
        "X-Process-Time-Ms",
    ]

    cors_allow_credentials: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        allowed_environments = {
            "development",
            "testing",
            "staging",
            "production",
        }

        normalized_value = value.lower().strip()

        if normalized_value not in allowed_environments:
            raise ValueError(
                "Environment must be one of: "
                f"{', '.join(sorted(allowed_environments))}"
            )

        return normalized_value

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        allowed_log_levels = {
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        }

        normalized_value = value.upper().strip()

        if normalized_value not in allowed_log_levels:
            raise ValueError(
                "Log level must be one of: "
                f"{', '.join(sorted(allowed_log_levels))}"
            )

        return normalized_value


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings instance.
    """

    return Settings()


settings = get_settings()