from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


PolicyDecision = Literal["ALLOW", "REVIEW", "DENY"]
PolicyRisk = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
ProposalStatus = Literal[
    "proposed",
    "review_required",
    "approved",
    "rejected",
    "applied",
    "rolled_back",
]


class GovernanceSignalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    action: str = Field(min_length=1, max_length=150)
    agent_id: str | None = Field(default=None, max_length=150)
    tenant_id: str | None = Field(default=None, max_length=150)
    incident_count: int = Field(default=0, ge=0)
    failure_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    error_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    destructive: bool = False
    write_access: bool = False
    handles_secrets: bool = False
    external_network: bool = False
    evidence: dict[str, Any] = Field(default_factory=dict)


class GovernanceSignalResponse(GovernanceSignalCreate):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PolicyRecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    action: str = Field(min_length=1, max_length=150)
    agent_id: str | None = Field(default=None, max_length=150)
    tenant_id: str | None = Field(default=None, max_length=150)
    window_size: int = Field(default=50, ge=1, le=500)


class PolicyRecommendationResponse(BaseModel):
    action: str
    recommended_decision: PolicyDecision
    recommended_risk: PolicyRisk
    confidence: float = Field(ge=0.0, le=1.0)
    reasons: list[str]
    signal_count: int
    failure_rate: float
    incident_count: int
    destructive_seen: bool
    auto_applied: bool = False


class PolicyProposalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    action: str = Field(min_length=1, max_length=150)
    recommended_decision: PolicyDecision
    recommended_risk: PolicyRisk
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(min_length=8, max_length=2000)
    tenant_id: str | None = Field(default=None, max_length=150)
    agent_id: str | None = Field(default=None, max_length=150)
    source_evidence: dict[str, Any] = Field(default_factory=dict)


class PolicyProposalResponse(BaseModel):
    id: UUID
    version: int
    action: str
    recommended_decision: PolicyDecision
    recommended_risk: PolicyRisk
    confidence: float
    rationale: str
    status: ProposalStatus
    auto_applied: bool
    tenant_id: str | None
    agent_id: str | None
    source_evidence: dict[str, Any]
    approved_by: UUID | None
    applied_at: datetime | None
    rolled_back_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProposalReviewRequest(BaseModel):
    approved: bool
    reason: str = Field(min_length=4, max_length=1000)


class ShadowEvaluationRequest(BaseModel):
    baseline_decision: PolicyDecision
    observed_actions: int = Field(default=1, ge=1)
    blocked_bad_actions: int = Field(default=0, ge=0)
    blocked_good_actions: int = Field(default=0, ge=0)
    escaped_bad_actions: int = Field(default=0, ge=0)


class ShadowEvaluationResponse(BaseModel):
    proposal_id: UUID
    safe_to_apply: bool
    score: float = Field(ge=0.0, le=1.0)
    reasons: list[str]


class ProposalApplyRequest(BaseModel):
    confirmation: Literal["APPLY_APPROVED_POLICY"]


class ProposalRollbackRequest(BaseModel):
    reason: str = Field(min_length=8, max_length=1000)


class GovernanceSummaryResponse(BaseModel):
    total_signals: int
    total_proposals: int
    review_required: int
    approved: int
    applied: int
    rolled_back: int
