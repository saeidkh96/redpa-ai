from __future__ import annotations

from typing import Any

from app.clients.external_http_client import ExternalHTTPClient
from app.tools.base import BaseTool


class BaseHTTPTool(BaseTool):
    """Base class for tools backed by external HTTP APIs."""

    def __init__(
        self,
        *,
        http_client: ExternalHTTPClient | None = None,
    ) -> None:
        self.http_client = http_client or ExternalHTTPClient()

    @staticmethod
    def required_string(
        arguments: dict[str, Any],
        key: str,
        *,
        max_length: int = 300,
    ) -> str:
        value = str(arguments.get(key, "") or "").strip()

        if not value:
            raise ValueError(f"'{key}' is required.")

        if len(value) > max_length:
            raise ValueError(
                f"'{key}' cannot exceed {max_length} characters."
            )

        return value

    @staticmethod
    def optional_string(
        arguments: dict[str, Any],
        key: str,
        *,
        default: str | None = None,
        max_length: int = 300,
    ) -> str | None:
        raw_value = arguments.get(key, default)

        if raw_value is None:
            return None

        value = str(raw_value).strip()

        if not value:
            return default

        if len(value) > max_length:
            raise ValueError(
                f"'{key}' cannot exceed {max_length} characters."
            )

        return value
