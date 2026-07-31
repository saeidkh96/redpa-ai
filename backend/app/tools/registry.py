from __future__ import annotations

from app.tools.base import BaseTool
from app.tools.calculator import CalculatorTool
from app.tools.datetime_tool import DateTimeTool
from app.tools.schemas import ToolMetadata


class ToolNotFoundError(Exception):
    """
    Raised when a requested tool is not registered.
    """


class ToolAlreadyRegisteredError(Exception):
    """
    Raised when a duplicate tool name is registered.
    """


class ToolRegistry:
    """
    Central registry for RedPA tools.
    """

    def __init__(
        self,
    ) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(
        self,
        tool: BaseTool,
    ) -> None:
        tool_name = self._normalize_tool_name(
            tool.metadata.name,
        )

        if tool_name in self._tools:
            raise ToolAlreadyRegisteredError(
                f"Tool '{tool_name}' is already registered."
            )

        self._tools[tool_name] = tool

    def get(
        self,
        tool_name: str,
    ) -> BaseTool:
        normalized_tool_name = self._normalize_tool_name(
            tool_name,
        )

        tool = self._tools.get(
            normalized_tool_name,
        )

        if tool is None:
            raise ToolNotFoundError(
                f"Tool '{normalized_tool_name}' is not registered."
            )

        return tool

    def has(
        self,
        tool_name: str,
    ) -> bool:
        normalized_tool_name = self._normalize_tool_name(
            tool_name,
        )

        return normalized_tool_name in self._tools

    def list_metadata(
        self,
    ) -> list[ToolMetadata]:
        return [
            tool.metadata
            for tool in self._tools.values()
        ]

    def list_names(
        self,
    ) -> list[str]:
        return sorted(
            self._tools.keys()
        )

    @staticmethod
    def _normalize_tool_name(
        tool_name: str,
    ) -> str:
        normalized_tool_name = str(
            tool_name,
        ).strip().casefold()

        if not normalized_tool_name:
            raise ValueError(
                "Tool name cannot be empty."
            )

        return normalized_tool_name


tool_registry = ToolRegistry()

tool_registry.register(
    CalculatorTool(),
)

tool_registry.register(
    DateTimeTool(),
)