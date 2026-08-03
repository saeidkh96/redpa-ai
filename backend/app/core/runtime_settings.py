from __future__ import annotations

import os
from dataclasses import dataclass


def _as_bool(
    value: str | None,
    default: bool = False,
) -> bool:
    if value is None:
        return default

    return value.strip().casefold() in {
        "1",
        "true",
        "yes",
        "on",
    }


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    environment: str
    debug: bool
    log_level: str
    json_logs: bool
    request_id_header: str
    correlation_id_header: str
    expose_error_details: bool

    @classmethod
    def load(
        cls,
    ) -> "RuntimeSettings":
        environment = os.getenv(
            "ENVIRONMENT",
            "development",
        ).strip()

        return cls(
            environment=environment,
            debug=_as_bool(
                os.getenv(
                    "DEBUG",
                ),
                default=False,
            ),
            log_level=os.getenv(
                "LOG_LEVEL",
                "INFO",
            ).upper(),
            json_logs=_as_bool(
                os.getenv(
                    "JSON_LOGS",
                ),
                default=True,
            ),
            request_id_header=os.getenv(
                "REQUEST_ID_HEADER",
                "X-Request-ID",
            ),
            correlation_id_header=os.getenv(
                "CORRELATION_ID_HEADER",
                "X-Correlation-ID",
            ),
            expose_error_details=_as_bool(
                os.getenv(
                    "EXPOSE_ERROR_DETAILS",
                ),
                default=(
                    environment
                    != "production"
                ),
            ),
        )
