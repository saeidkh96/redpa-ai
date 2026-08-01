from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


ToolSource = Literal[
    "internal",
    "mcp",
]


class UnifiedToolInfo(BaseModel):
    """
    Stable public representation of an internal or MCP tool.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    qualified_name: str = Field(
        min_length=1,
        max_length=400,
    )

    source: ToolSource

    name: str = Field(
        min_length=1,
        max_length=200,
    )

    display_name: str | None = Field(
        default=None,
        max_length=300,
    )

    description: str | None = Field(
        default=None,
        max_length=4000,
    )

    version: str | None = Field(
        default=None,
        max_length=100,
    )

    server_name: str | None = Field(
        default=None,
        max_length=100,
    )

    requires_approval: bool

    input_schema: dict[str, Any] = Field(
        default_factory=dict,
    )


class UnifiedToolCatalogResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    items: list[UnifiedToolInfo] = Field(
        default_factory=list,
    )

    total: int = Field(
        ge=0,
    )

    internal_total: int = Field(
        ge=0,
    )

    mcp_total: int = Field(
        ge=0,
    )

    mcp_server_errors: dict[str, str] = Field(
        default_factory=dict,
    )

    refreshed_at: datetime


class UnifiedToolCatalogStatusResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    cached: bool
    total: int = Field(
        ge=0,
    )
    refreshed_at: datetime | None = None
