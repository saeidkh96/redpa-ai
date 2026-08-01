from __future__ import annotations

from typing import Final

from prometheus_client import Counter, Histogram


TOOL_EXECUTIONS_TOTAL: Final[Counter] = Counter(
    name="redpa_tool_executions_total",
    documentation="Total number of RedPA tool execution attempts.",
    labelnames=("tool_name", "status"),
)

TOOL_ERRORS_TOTAL: Final[Counter] = Counter(
    name="redpa_tool_errors_total",
    documentation="Total number of RedPA tool execution errors.",
    labelnames=("tool_name", "error_type"),
)

TOOL_EXECUTION_DURATION_SECONDS: Final[Histogram] = Histogram(
    name="redpa_tool_execution_duration_seconds",
    documentation="RedPA tool execution duration in seconds.",
    labelnames=("tool_name", "status"),
    buckets=(
        0.0001, 0.0005, 0.001, 0.0025, 0.005, 0.01,
        0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0,
    ),
)


class ToolMetrics:
    SUCCESS_STATUS: Final[str] = "success"
    ERROR_STATUS: Final[str] = "error"
    NOT_FOUND_STATUS: Final[str] = "not_found"

    @classmethod
    def record_execution(
        cls,
        *,
        tool_name: str,
        status: str,
        duration_seconds: float,
    ) -> None:
        tool = cls._normalize_label(tool_name, fallback="unknown")
        normalized_status = cls._normalize_status(status)
        duration = max(float(duration_seconds), 0.0)

        TOOL_EXECUTIONS_TOTAL.labels(
            tool_name=tool,
            status=normalized_status,
        ).inc()

        TOOL_EXECUTION_DURATION_SECONDS.labels(
            tool_name=tool,
            status=normalized_status,
        ).observe(duration)

    @classmethod
    def record_error(
        cls,
        *,
        tool_name: str,
        error_type: str,
    ) -> None:
        TOOL_ERRORS_TOTAL.labels(
            tool_name=cls._normalize_label(
                tool_name,
                fallback="unknown",
            ),
            error_type=cls._normalize_label(
                error_type,
                fallback="unknown_error",
            ),
        ).inc()

    @classmethod
    def record_success(
        cls,
        *,
        tool_name: str,
        duration_seconds: float,
    ) -> None:
        cls.record_execution(
            tool_name=tool_name,
            status=cls.SUCCESS_STATUS,
            duration_seconds=duration_seconds,
        )

    @classmethod
    def record_failure(
        cls,
        *,
        tool_name: str,
        duration_seconds: float,
        error_type: str,
        status: str = ERROR_STATUS,
    ) -> None:
        cls.record_execution(
            tool_name=tool_name,
            status=status,
            duration_seconds=duration_seconds,
        )
        cls.record_error(
            tool_name=tool_name,
            error_type=error_type,
        )

    @classmethod
    def _normalize_status(cls, value: str) -> str:
        normalized = cls._normalize_label(
            value,
            fallback=cls.ERROR_STATUS,
        )
        if normalized not in {
            cls.SUCCESS_STATUS,
            cls.ERROR_STATUS,
            cls.NOT_FOUND_STATUS,
        }:
            return cls.ERROR_STATUS
        return normalized

    @staticmethod
    def _normalize_label(
        value: str,
        *,
        fallback: str,
    ) -> str:
        normalized = str(value or fallback).strip().casefold()
        if not normalized:
            return fallback

        cleaned = "".join(
            character
            if character.isalnum() or character in {"_", "-", "."}
            else "_"
            for character in normalized
        ).strip("_")

        return (cleaned or fallback)[:100]
