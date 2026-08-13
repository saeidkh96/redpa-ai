from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ServiceState(BaseModel):
    status: str


class Health(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    database: ServiceState


class AgentCard(BaseModel):
    model_config = {"extra": "allow"}

    id: str | None = None
    name: str | None = None


class AgentList(BaseModel):
    model_config = {"extra": "allow"}

    items: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0


class Provider(BaseModel):
    name: str
    provider_type: str
    default_model: str
    capabilities: list[str]
    enabled: bool


class ProviderHealth(BaseModel):
    provider: str
    available: bool
    models: list[str]
    detail: str | None = None


class ReliabilityProvider(BaseModel):
    provider: str
    available: bool
    circuit_state: str
    failures: int
    failure_threshold: int
    score: float
    status: str


class ReliabilityScorecard(BaseModel):
    overall_score: float
    healthy_providers: int
    degraded_providers: int
    unavailable_providers: int
    providers: list[ReliabilityProvider]


class ReleaseGateResult(BaseModel):
    id: str
    decision: str
    reasons: list[str]
    release_label: str | None = None
    regression: dict[str, Any]
    created_at: str


class ToolCatalog(BaseModel):
    model_config = {"extra": "allow"}

    items: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0
    internal_total: int = 0
    mcp_total: int = 0
    mcp_server_errors: dict[str, str] = Field(default_factory=dict)
    refreshed_at: str
