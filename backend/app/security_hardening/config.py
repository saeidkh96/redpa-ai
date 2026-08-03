from __future__ import annotations

import os
from dataclasses import dataclass


class EnvironmentValidationError(
    RuntimeError,
):
    pass


@dataclass(frozen=True, slots=True)
class SecuritySettings:
    environment: str
    secret_key: str
    database_url: str
    redis_url: str
    allowed_hosts: tuple[str, ...]
    require_https: bool

    @classmethod
    def load(
        cls,
    ) -> "SecuritySettings":
        environment = os.getenv(
            "ENVIRONMENT",
            "development",
        ).strip()

        secret_key = os.getenv(
            "SECRET_KEY",
            "",
        ).strip()

        database_url = os.getenv(
            "DATABASE_URL",
            "",
        ).strip()

        redis_url = os.getenv(
            "REDIS_URL",
            "",
        ).strip()

        allowed_hosts = tuple(
            host.strip()
            for host in os.getenv(
                "ALLOWED_HOSTS",
                "localhost,127.0.0.1",
            ).split(",")
            if host.strip()
        )

        require_https = os.getenv(
            "REQUIRE_HTTPS",
            "false",
        ).casefold() in {
            "1",
            "true",
            "yes",
            "on",
        }

        errors: list[str] = []

        if not database_url:
            errors.append(
                "DATABASE_URL is required."
            )

        if not redis_url:
            errors.append(
                "REDIS_URL is required."
            )

        if environment == "production":
            if len(secret_key) < 32:
                errors.append(
                    "SECRET_KEY must contain at least 32 characters in production."
                )

            if "*" in allowed_hosts:
                errors.append(
                    "Wildcard ALLOWED_HOSTS is not permitted in production."
                )

        if errors:
            raise EnvironmentValidationError(
                " ".join(
                    errors,
                )
            )

        return cls(
            environment=environment,
            secret_key=secret_key,
            database_url=database_url,
            redis_url=redis_url,
            allowed_hosts=allowed_hosts,
            require_https=require_https,
        )
