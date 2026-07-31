from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.tools.schemas import (
    ToolExecutionResult,
    ToolMetadata,
)


class BaseTool(ABC):
    """
    Base interface for every RedPA tool.

    Every tool must provide metadata and implement the execute method.
    """

    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """
        Return tool metadata.
        """

        raise NotImplementedError

    @abstractmethod
    async def execute(
        self,
        arguments: dict[str, Any],
    ) -> ToolExecutionResult:
        """
        Execute the tool using validated arguments.
        """

        raise NotImplementedError