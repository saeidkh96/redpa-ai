from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.guardrails.contracts import GuardrailDecision, RiskLevel


class PolicyOverrideCreate(BaseModel):
    action: str = Field(min_length=1, max_length=300)
    boundary: str = Field(default="tool", min_length=1, max_length=50)
    resource: str | None = Field(default=None, max_length=200)
    decision: GuardrailDecision
    risk: RiskLevel
    reason: str = Field(min_length=3, max_length=2000)
    enabled: bool = True


class PolicyOverrideUpdate(BaseModel):
    resource: str | None = Field(default=None, max_length=200)
    decision: GuardrailDecision | None = None
    risk: RiskLevel | None = None
    reason: str | None = Field(default=None, min_length=3, max_length=2000)
    enabled: bool | None = None


class PolicyOverrideResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    action: str
    boundary: str
    resource: str | None
    decision: str
    risk: str
    reason: str
    enabled: bool
    created_at: datetime
    updated_at: datetime
