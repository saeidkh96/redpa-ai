from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.guardrails.contracts import GuardrailDecision, RiskLevel


class PolicyEnforcementRequest(BaseModel):
    action: str = Field(min_length=1, max_length=300)
    boundary: str = Field(default="tool", max_length=50)
    resource: str | None = Field(default=None, max_length=200)
    arguments: dict[str, Any] = Field(default_factory=dict)
    conversation_id: uuid.UUID | None = None
    message_id: uuid.UUID | None = None
    workflow_id: str | None = Field(default=None, max_length=150)
    request_content: str | None = Field(default=None, max_length=10000)
    approval_granted: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class PolicyEnforcementResponse(BaseModel):
    decision: GuardrailDecision
    risk: RiskLevel
    reason: str
    matched_rules: list[str]
    policy_version: str
    source: str
    executable: bool
    review_id: uuid.UUID | None = None


class PolicyAuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID | None
    conversation_id: uuid.UUID | None
    review_id: uuid.UUID | None
    boundary: str
    action: str
    resource: str | None
    decision: str
    risk: str
    reason: str
    matched_rules: list[str]
    policy_version: str
    source: str
    event_metadata: dict[str, Any]
    created_at: datetime
