from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application configuration.
    """

    app_name: str = Field(
        default="RedPA AI",
        alias="APP_NAME",
    )

    app_version: str = Field(
        default="0.1.0",
        alias="APP_VERSION",
    )

    environment: Literal[
        "development",
        "testing",
        "staging",
        "production",
    ] = Field(
        default="development",
        alias="ENVIRONMENT",
    )

    debug: bool = Field(
        default=False,
        alias="DEBUG",
    )

    api_v1_prefix: str = Field(
        default="/api/v1",
        alias="API_V1_PREFIX",
    )

    database_url: str = Field(
        alias="DATABASE_URL",
    )

    cors_allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ],
        alias="CORS_ALLOWED_ORIGINS",
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()