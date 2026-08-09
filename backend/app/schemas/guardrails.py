from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.guardrails.contracts import (
    GuardrailDecision,
    RiskLevel,
)


class GuardrailEvaluationRequest(BaseModel):
    action: str = Field(min_length=1, max_length=200)
    resource: str | None = Field(default=None, max_length=200)
    arguments: dict[str, Any] = Field(default_factory=dict)
    agent_id: str | None = Field(default=None, max_length=150)
    workflow_id: str | None = Field(default=None, max_length=150)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GuardrailEvaluationResponse(BaseModel):
    decision: GuardrailDecision
    risk: RiskLevel
    reason: str
    matched_rules: list[str]
    policy_version: str
    source: str


class GuardrailHealthResponse(BaseModel):
    policy_service: str
