from __future__ import annotations

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class ToolDiscoveryResponse(BaseModel):
    """
    Public metadata returned for one registered RedPA tool.

    from_attributes=True allows this schema to validate both:
    - dictionaries returned by ToolService.list_tools()
    - ToolMetadata Pydantic objects returned by get_tool_metadata()
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        from_attributes=True,
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
        min_length=1,
        max_length=50,
    )

    requires_approval: bool


class ToolDiscoveryListResponse(BaseModel):
    """
    Response returned when listing all registered tools.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    items: list[ToolDiscoveryResponse] = Field(
        default_factory=list,
    )

    total: int = Field(
        ge=0,
    )
