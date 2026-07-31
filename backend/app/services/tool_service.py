from __future__ import annotations

import logging
import time
from typing import Any

from app.tools.registry import (
    ToolNotFoundError,
    tool_registry,
)
from app.tools.schemas import ToolExecutionResult


logger = logging.getLogger(__name__)


class ToolService:
    """
    Application service responsible for executing registered tools.
    """

    @classmethod
    async def execute(
        cls,
        *,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> ToolExecutionResult:
        started_at = time.perf_counter()

        try:
            tool = tool_registry.get(
                tool_name,
            )

        except ToolNotFoundError as exception:
            execution_time_ms = (
                time.perf_counter() - started_at
            ) * 1000

            logger.warning(
                "Tool was not found | tool=%s",
                tool_name,
            )

            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=str(exception),
                execution_time_ms=round(
                    execution_time_ms,
                    2,
                ),
                metadata={},
            )

        logger.info(
            "Executing tool | tool=%s arguments=%s",
            tool.metadata.name,
            arguments,
        )

        try:
            execution_result = await tool.execute(
                arguments,
            )

        except Exception as exception:
            execution_time_ms = (
                time.perf_counter() - started_at
            ) * 1000

            logger.exception(
                "Unhandled tool execution error | tool=%s",
                tool.metadata.name,
            )

            return ToolExecutionResult(
                tool_name=tool.metadata.name,
                success=False,
                result=None,
                error=cls._format_error(
                    exception,
                ),
                execution_time_ms=round(
                    execution_time_ms,
                    2,
                ),
                metadata={},
            )

        logger.info(
            "Tool execution completed | tool=%s "
            "success=%s execution_time_ms=%.2f",
            execution_result.tool_name,
            execution_result.success,
            execution_result.execution_time_ms,
        )

        return execution_result

    @staticmethod
    def list_tools() -> list[dict[str, Any]]:
        return [
            metadata.model_dump()
            for metadata in (
                tool_registry.list_metadata()
            )
        ]

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