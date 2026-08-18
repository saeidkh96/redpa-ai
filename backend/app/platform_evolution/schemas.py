from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class EvolutionRecordResponse(BaseModel):
    id: uuid.UUID
    version: int
    kind: str
    status: str
    summary: str
    payload: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class EvolutionListResponse(BaseModel):
    items: list[EvolutionRecordResponse]
    total: int


class ReliabilitySignalRequest(BaseModel):
    service: str = Field(min_length=1, max_length=150)
    health: Literal["healthy", "degraded", "unhealthy"]
    error_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    latency_ms: float = Field(default=0.0, ge=0.0)


class AgentFailoverRequest(BaseModel):
    task: str = Field(min_length=1, max_length=500)
    candidates: list[str] = Field(min_length=1)
    unhealthy_agents: list[str] = Field(default_factory=list)


class AdaptivePolicyRequest(BaseModel):
    action: str = Field(min_length=1, max_length=150)
    incident_count: int = Field(default=0, ge=0)
    failure_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    destructive: bool = False

    # V13-compatible optional evidence dimensions.
    agent_id: str | None = Field(default=None, max_length=150)
    tenant_id: str | None = Field(default=None, max_length=150)
    error_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    write_access: bool = False
    handles_secrets: bool = False
    external_network: bool = False


class ComplianceEvidenceRequest(BaseModel):
    control: str = Field(min_length=1, max_length=150)
    evidence: dict[str, Any] = Field(default_factory=dict)
    required_fields: list[str] = Field(default_factory=list)


class CloudReadinessRequest(BaseModel):
    environment: str = Field(min_length=1, max_length=80)
    health_checks: bool = True
    backups: bool = False
    secrets_manager: bool = False
    autoscaling: bool = False
    telemetry: bool = True


class RolloutDecisionRequest(BaseModel):
    candidate: str = Field(min_length=1, max_length=150)
    baseline_score: float = Field(ge=0.0, le=1.0)
    candidate_score: float = Field(ge=0.0, le=1.0)
    error_rate_delta: float = Field(default=0.0, ge=-1.0, le=1.0)


class ConnectorAssessmentRequest(BaseModel):
    connector: str = Field(min_length=1, max_length=150)
    write_access: bool = False
    external_network: bool = True
    handles_secrets: bool = False
    approval_required: bool = False


class AgentRegistrationRequest(BaseModel):
    agent_id: str = Field(min_length=1, max_length=150)
    version: str = Field(min_length=1, max_length=80)
    capabilities: list[str] = Field(default_factory=list)
    signed_manifest: bool = False
    health_endpoint: bool = False
    governance_compatible: bool = True
