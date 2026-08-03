from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RemoteAgentRegistrationRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    name: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9][a-z0-9_-]*$",
    )
    base_url: str = Field(
        min_length=8,
        max_length=500,
    )
    enabled: bool = True
    timeout_seconds: float = Field(
        default=30.0,
        ge=1.0,
        le=120.0,
    )


class RemoteAgentSummary(BaseModel):
    name: str
    base_url: str
    enabled: bool
    connected: bool
    agent_name: str | None = None
    agent_version: str | None = None
    protocol_bindings: list[str] = Field(
        default_factory=list,
    )
    skills: list[str] = Field(
        default_factory=list,
    )
    last_checked_at: datetime | None = None
    error: str | None = None


class RemoteAgentListResponse(BaseModel):
    items: list[RemoteAgentSummary]
    total: int


class RemoteAgentCardResponse(BaseModel):
    name: str
    base_url: str
    card: dict[str, Any]


class RemoteDelegationRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    message: str = Field(
        min_length=1,
        max_length=20_000,
    )
    timeout_seconds: float = Field(
        default=60.0,
        ge=1.0,
        le=300.0,
    )


class RemoteDelegationResponse(BaseModel):
    remote_agent: str
    base_url: str
    success: bool
    final_response: dict[str, Any] | None
    events: list[dict[str, Any]]
    event_count: int
    execution_time_ms: float
    error: str | None = None
