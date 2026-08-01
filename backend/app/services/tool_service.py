from __future__ import annotations

import logging
import time
from typing import Any

from app.monitoring.tool_metrics import ToolMetrics
from app.tools.registry import (
    ToolNotFoundError,
    tool_registry,
)
from app.tools.schemas import (
    ToolExecutionResult,
    ToolMetadata,
)


logger = logging.getLogger(__name__)


class ToolService:
    """
    Execute and discover registered RedPA tools.

    Tool execution attempts are recorded through Prometheus metrics.
    Discovery methods expose only stable tool metadata and never
    execute tools.
    """

    @classmethod
    async def execute(
        cls,
        *,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> ToolExecutionResult:
        started_at = time.perf_counter()

        normalized_tool_name = cls._normalize_tool_name(
            tool_name,
        )

        try:
            tool = tool_registry.get(
                normalized_tool_name,
            )

        except ToolNotFoundError as exception:
            duration_seconds = cls._elapsed_seconds(
                started_at,
            )

            logger.warning(
                "Tool was not found | tool=%s",
                normalized_tool_name,
            )

            ToolMetrics.record_failure(
                tool_name=normalized_tool_name,
                duration_seconds=duration_seconds,
                error_type="tool_not_found",
                status=ToolMetrics.NOT_FOUND_STATUS,
            )

            return ToolExecutionResult(
                tool_name=normalized_tool_name,
                success=False,
                result=None,
                error=str(exception),
                execution_time_ms=(
                    cls._seconds_to_milliseconds(
                        duration_seconds,
                    )
                ),
                metadata={},
            )

        registered_tool_name = cls._normalize_tool_name(
            tool.metadata.name,
        )

        logger.info(
            "Executing tool | tool=%s arguments=%s",
            registered_tool_name,
            cls._safe_arguments_for_log(
                arguments,
            ),
        )

        try:
            execution_result = await tool.execute(
                arguments,
            )

        except Exception as exception:
            duration_seconds = cls._elapsed_seconds(
                started_at,
            )

            error_type = type(
                exception,
            ).__name__

            logger.exception(
                "Unhandled tool execution error | tool=%s",
                registered_tool_name,
            )

            ToolMetrics.record_failure(
                tool_name=registered_tool_name,
                duration_seconds=duration_seconds,
                error_type=error_type,
            )

            return ToolExecutionResult(
                tool_name=registered_tool_name,
                success=False,
                result=None,
                error=cls._format_error(
                    exception,
                ),
                execution_time_ms=(
                    cls._seconds_to_milliseconds(
                        duration_seconds,
                    )
                ),
                metadata={},
            )

        duration_seconds = cls._elapsed_seconds(
            started_at,
        )

        normalized_result = (
            cls._normalize_execution_result(
                execution_result=execution_result,
                fallback_tool_name=(
                    registered_tool_name
                ),
                duration_seconds=duration_seconds,
            )
        )

        if normalized_result.success:
            ToolMetrics.record_success(
                tool_name=normalized_result.tool_name,
                duration_seconds=duration_seconds,
            )

        else:
            ToolMetrics.record_failure(
                tool_name=normalized_result.tool_name,
                duration_seconds=duration_seconds,
                error_type=(
                    cls._resolve_result_error_type(
                        normalized_result,
                    )
                ),
            )

        logger.info(
            "Tool execution completed | tool=%s "
            "success=%s execution_time_ms=%.2f",
            normalized_result.tool_name,
            normalized_result.success,
            normalized_result.execution_time_ms,
        )

        return normalized_result

    @staticmethod
    def list_tools() -> list[dict[str, Any]]:
        """
        Return serializable metadata for every registered tool.
        """

        return [
            metadata.model_dump()
            for metadata in tool_registry.list_metadata()
        ]

    @staticmethod
    def get_tool_metadata(
        *,
        tool_name: str,
    ) -> ToolMetadata:
        """
        Return metadata for one registered tool.

        ToolNotFoundError is intentionally allowed to propagate so
        the API layer can convert it to HTTP 404.
        """

        tool = tool_registry.get(
            tool_name,
        )

        return tool.metadata

    @classmethod
    def _normalize_execution_result(
        cls,
        *,
        execution_result: ToolExecutionResult,
        fallback_tool_name: str,
        duration_seconds: float,
    ) -> ToolExecutionResult:
        result_tool_name = cls._normalize_tool_name(
            execution_result.tool_name
            or fallback_tool_name,
        )

        execution_time_ms = (
            execution_result.execution_time_ms
        )

        if execution_time_ms < 0:
            execution_time_ms = (
                cls._seconds_to_milliseconds(
                    duration_seconds,
                )
            )

        return ToolExecutionResult(
            tool_name=result_tool_name,
            success=execution_result.success,
            result=execution_result.result,
            error=execution_result.error,
            execution_time_ms=round(
                execution_time_ms,
                2,
            ),
            metadata=execution_result.metadata or {},
        )

    @staticmethod
    def _resolve_result_error_type(
        execution_result: ToolExecutionResult,
    ) -> str:
        metadata = execution_result.metadata

        if isinstance(
            metadata,
            dict,
        ):
            metadata_error_type = metadata.get(
                "error_type",
            )

            if metadata_error_type:
                return str(
                    metadata_error_type,
                )

        if execution_result.error:
            return "tool_validation_error"

        return "tool_execution_failed"

    @staticmethod
    def _safe_arguments_for_log(
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        protected_keys = {
            "password",
            "token",
            "access_token",
            "refresh_token",
            "authorization",
            "api_key",
            "secret",
        }

        safe_arguments: dict[str, Any] = {}

        for key, value in arguments.items():
            normalized_key = str(
                key,
            ).casefold()

            if normalized_key in protected_keys:
                safe_arguments[str(key)] = "[REDACTED]"
                continue

            rendered_value = repr(
                value,
            )

            if len(rendered_value) > 300:
                rendered_value = (
                    rendered_value[:297]
                    + "..."
                )

            safe_arguments[str(key)] = rendered_value

        return safe_arguments

    @staticmethod
    def _normalize_tool_name(
        tool_name: str,
    ) -> str:
        normalized_tool_name = str(
            tool_name or "unknown",
        ).strip().casefold()

        if not normalized_tool_name:
            return "unknown"

        return normalized_tool_name

    @staticmethod
    def _elapsed_seconds(
        started_at: float,
    ) -> float:
        return max(
            time.perf_counter() - started_at,
            0.0,
        )

    @staticmethod
    def _seconds_to_milliseconds(
        duration_seconds: float,
    ) -> float:
        return round(
            duration_seconds * 1000,
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
