from __future__ import annotations

from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class ToolMetadata(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    name: str = Field(
        min_length=1,
        max_length=100,
    )

    description: str = Field(
        min_length=1,
        max_length=1000,
    )

    version: str = Field(
        default="1.0.0",
        min_length=1,
        max_length=50,
    )

    requires_approval: bool = False


class ToolExecutionRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    tool_name: str = Field(
        min_length=1,
        max_length=100,
    )

    arguments: dict[str, Any] = Field(
        default_factory=dict,
    )


class ToolExecutionResult(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    tool_name: str = Field(
        min_length=1,
        max_length=100,
    )

    success: bool

    result: Any | None = None

    error: str | None = None

    execution_time_ms: float = Field(
        default=0.0,
        ge=0.0,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )