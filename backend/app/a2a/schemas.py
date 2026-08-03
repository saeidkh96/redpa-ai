from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentStatus(StrEnum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    OFFLINE = "offline"


class AgentCapability(BaseModel):
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
        max_length=500,
    )
    tags: list[str] = Field(
        default_factory=list,
    )
    input_modes: list[str] = Field(
        default_factory=lambda: ["text"],
    )
    output_modes: list[str] = Field(
        default_factory=lambda: ["text"],
    )
    examples: list[str] = Field(
        default_factory=list,
    )


class AgentEndpoint(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    url: str = Field(
        min_length=1,
        max_length=500,
    )
    transport: str = Field(
        default="internal",
        min_length=1,
        max_length=50,
    )


class AgentCard(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    id: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9][a-z0-9_-]*$",
    )
    name: str = Field(
        min_length=1,
        max_length=120,
    )
    version: str = Field(
        min_length=1,
        max_length=50,
    )
    description: str = Field(
        min_length=1,
        max_length=1_000,
    )
    status: AgentStatus = AgentStatus.ACTIVE
    capabilities: list[AgentCapability]
    supported_routes: list[str] = Field(
        default_factory=list,
    )
    endpoint: AgentEndpoint | None = None
    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )
    registered_at: datetime
    updated_at: datetime


class AgentCardSummary(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    id: str
    name: str
    version: str
    status: AgentStatus
    capability_names: list[str]
    supported_routes: list[str]


class AgentListResponse(BaseModel):
    items: list[AgentCardSummary]
    total: int


class AgentHealthItem(BaseModel):
    id: str
    name: str
    status: AgentStatus
    capability_count: int


class AgentHealthResponse(BaseModel):
    status: str
    total_agents: int
    active_agents: int
    degraded_agents: int
    offline_agents: int
    checked_at: datetime
    agents: list[AgentHealthItem]


class CapabilityMatch(BaseModel):
    agent_id: str
    agent_name: str
    capability_name: str
    capability_description: str
    matched_tags: list[str]
    score: float


class CapabilityDiscoveryResponse(BaseModel):
    query: str
    matches: list[CapabilityMatch]
    total: int
