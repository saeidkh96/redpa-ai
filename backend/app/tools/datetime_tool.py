from __future__ import annotations

from datetime import datetime
from time import perf_counter
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.tools.base import BaseTool
from app.tools.schemas import (
    ToolExecutionResult,
    ToolMetadata,
)


class DateTimeTool(BaseTool):
    """
    Return the current date and time for an IANA timezone.

    This tool is self-contained and must not import ToolService,
    the registry, or any application service. ToolService is
    responsible for calling the tool, not the other way around.
    """

    @property
    def metadata(
        self,
    ) -> ToolMetadata:
        return ToolMetadata(
            name="datetime",
            description=(
                "Returns the current date, time, weekday, UTC offset, "
                "and ISO datetime for a requested IANA timezone such "
                "as UTC, Europe/Berlin, Asia/Tehran, or Asia/Tokyo."
            ),
            version="1.0.0",
            requires_approval=False,
        )

    async def execute(
        self,
        arguments: dict[str, Any],
    ) -> ToolExecutionResult:
        started_at = perf_counter()

        timezone_name = self._normalize_timezone(
            arguments.get(
                "timezone",
                "UTC",
            )
        )

        try:
            timezone = ZoneInfo(
                timezone_name,
            )

            current_datetime = datetime.now(
                timezone,
            )

            return ToolExecutionResult(
                tool_name=self.metadata.name,
                success=True,
                result={
                    "date": current_datetime.strftime(
                        "%Y-%m-%d",
                    ),
                    "time": current_datetime.strftime(
                        "%H:%M:%S",
                    ),
                    "datetime": current_datetime.isoformat(),
                    "timezone": timezone_name,
                    "utc_offset": current_datetime.strftime(
                        "%z",
                    ),
                    "weekday": current_datetime.strftime(
                        "%A",
                    ),
                },
                error=None,
                execution_time_ms=self._elapsed_ms(
                    started_at,
                ),
                metadata={
                    "timezone": timezone_name,
                },
            )

        except ZoneInfoNotFoundError:
            return ToolExecutionResult(
                tool_name=self.metadata.name,
                success=False,
                result=None,
                error=(
                    f"Unknown timezone '{timezone_name}'. "
                    "Use a valid IANA timezone such as "
                    "'UTC', 'Europe/Berlin', or 'Asia/Tehran'."
                ),
                execution_time_ms=self._elapsed_ms(
                    started_at,
                ),
                metadata={
                    "timezone": timezone_name,
                },
            )

        except Exception as exception:
            return ToolExecutionResult(
                tool_name=self.metadata.name,
                success=False,
                result=None,
                error=self._format_error(
                    exception,
                ),
                execution_time_ms=self._elapsed_ms(
                    started_at,
                ),
                metadata={
                    "timezone": timezone_name,
                },
            )

    @staticmethod
    def _normalize_timezone(
        value: Any,
    ) -> str:
        timezone_name = str(
            value or "UTC",
        ).strip()

        if not timezone_name:
            return "UTC"

        aliases: dict[str, str] = {
            "utc": "UTC",
            "gmt": "UTC",
            "berlin": "Europe/Berlin",
            "germany": "Europe/Berlin",
            "deutschland": "Europe/Berlin",
            "passau": "Europe/Berlin",
            "london": "Europe/London",
            "paris": "Europe/Paris",
            "tokyo": "Asia/Tokyo",
            "tehran": "Asia/Tehran",
            "iran": "Asia/Tehran",
            "new york": "America/New_York",
            "new_york": "America/New_York",
            "newyork": "America/New_York",
        }

        return aliases.get(
            timezone_name.casefold(),
            timezone_name,
        )

    @staticmethod
    def _elapsed_ms(
        started_at: float,
    ) -> float:
        return round(
            (
                perf_counter()
                - started_at
            )
            * 1000,
            2,
        )

    @staticmethod
    def _format_error(
        exception: Exception,
    ) -> str:
        exception_message = str(
            exception,
        ).strip()

        if not exception_message:
            return type(exception).__name__

        return (
            f"{type(exception).__name__}: "
            f"{exception_message}"
        )[:1000]