from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
)


MCPServerStatus = Literal[
    "connected",
    "unavailable",
    "disabled",
]

MCPPlatformStatus = Literal[
    "healthy",
    "degraded",
    "unavailable",
]


class MCPServerConfig(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    name: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_.-]+$",
    )
    transport: Literal["streamable_http"] = "streamable_http"
    url: HttpUrl
    enabled: bool = True
    description: str | None = Field(
        default=None,
        max_length=500,
    )
    headers: dict[str, str] = Field(
        default_factory=dict,
    )
    timeout_seconds: float = Field(
        default=30.0,
        gt=0.0,
        le=300.0,
    )
    requires_approval: bool = True
    allowed_tools: list[str] | None = None

    @field_validator("headers")
    @classmethod
    def validate_headers(
        cls,
        value: dict[str, str],
    ) -> dict[str, str]:
        protected_names = {
            "host",
            "content-length",
            "transfer-encoding",
        }

        normalized_headers: dict[str, str] = {}

        for raw_name, raw_value in value.items():
            name = str(
                raw_name,
            ).strip()
            header_value = str(
                raw_value,
            ).strip()

            if not name or not header_value:
                raise ValueError(
                    "MCP header names and values cannot be empty."
                )

            if name.casefold() in protected_names:
                raise ValueError(
                    f"MCP header '{name}' cannot be configured."
                )

            normalized_headers[name] = header_value

        return normalized_headers


class MCPServerListConfig(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    servers: list[MCPServerConfig] = Field(
        default_factory=list,
    )


class MCPToolInfo(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    server_name: str
    name: str
    qualified_name: str | None = None
    title: str | None = None
    description: str | None = None
    input_schema: dict[str, Any] = Field(
        default_factory=dict,
    )
    requires_approval: bool = True


class MCPServerInfo(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    name: str
    description: str | None = None
    transport: str
    url: str
    enabled: bool
    requires_approval: bool


class MCPServerHealth(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    name: str
    enabled: bool
    status: MCPServerStatus
    tool_count: int = Field(
        ge=0,
    )
    latency_ms: float = Field(
        ge=0.0,
    )
    error: str | None = None
    checked_at: datetime


class MCPHealthResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    status: MCPPlatformStatus
    configured_servers: int = Field(
        ge=0,
    )
    enabled_servers: int = Field(
        ge=0,
    )
    connected_servers: int = Field(
        ge=0,
    )
    unavailable_servers: int = Field(
        ge=0,
    )
    total_tools: int = Field(
        ge=0,
    )
    checked_at: datetime
    servers: list[MCPServerHealth] = Field(
        default_factory=list,
    )


class MCPToolCatalogResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    items: list[MCPToolInfo] = Field(
        default_factory=list,
    )
    total: int = Field(
        ge=0,
    )
    server_errors: dict[str, str] = Field(
        default_factory=dict,
    )
    cached: bool = False


class MCPReloadResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    configured_servers: int = Field(
        ge=0,
    )
    message: str


class MCPToolCallResult(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    server_name: str
    tool_name: str
    success: bool
    is_error: bool
    content: list[dict[str, Any]] = Field(
        default_factory=list,
    )
    structured_content: Any = None
    execution_time_ms: float = Field(
        ge=0.0,
    )


class MCPToolCallRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    arguments: dict[str, Any] = Field(
        default_factory=dict,
    )
    approval_granted: bool = False


class MCPQualifiedToolCallRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    qualified_name: str = Field(
        min_length=7,
        max_length=500,
        examples=[
            "mcp:example-remote:search",
        ],
    )
    arguments: dict[str, Any] = Field(
        default_factory=dict,
    )
    approval_granted: bool = False
