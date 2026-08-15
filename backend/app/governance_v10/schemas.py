from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.evaluation import EvaluationMetric
from app.models.governance_v10 import AgentRunStatus
from app.schemas.evaluation import EvaluationInput


class AgentRunCreate(BaseModel):
    agent_id: str = Field(min_length=1, max_length=150)
    objective: str = Field(min_length=1, max_length=20000)
    workflow_id: str | None = Field(default=None, max_length=150)
    model_name: str | None = Field(default=None, max_length=200)
    input_payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentRunUpdate(BaseModel):
    status: AgentRunStatus
    output_payload: dict[str, Any] = Field(default_factory=dict)
    error: str | None = Field(default=None, max_length=20000)


class AgentRunEventCreate(BaseModel):
    event_type: str = Field(min_length=1, max_length=80)
    stage: str | None = Field(default=None, max_length=120)
    payload: dict[str, Any] = Field(default_factory=dict)


class AgentRunEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    run_id: uuid.UUID
    event_type: str
    stage: str | None
    trace_id: str | None
    span_id: str | None
    payload: dict[str, Any]
    created_at: datetime


class AgentRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    agent_id: str
    workflow_id: str | None
    trace_id: str | None
    status: AgentRunStatus
    objective: str
    model_name: str | None
    input_payload: dict[str, Any]
    output_payload: dict[str, Any]
    run_metadata: dict[str, Any]
    evaluation_run_id: uuid.UUID | None
    evaluation_score: float | None
    error: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    events: list[AgentRunEventResponse] = Field(default_factory=list)


class AgentRunListResponse(BaseModel):
    items: list[AgentRunResponse]
    total: int
    limit: int
    offset: int


class RunPolicyCheckRequest(BaseModel):
    action: str = Field(min_length=1, max_length=300)
    boundary: str = Field(default="tool", max_length=50)
    resource: str | None = Field(default=None, max_length=200)
    arguments: dict[str, Any] = Field(default_factory=dict)
    conversation_id: uuid.UUID | None = None
    message_id: uuid.UUID | None = None
    request_content: str | None = Field(default=None, max_length=10000)
    approval_granted: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class RunPolicyCheckResponse(BaseModel):
    run_id: uuid.UUID
    decision: str
    risk: str
    reason: str
    matched_rules: list[str]
    policy_version: str
    source: str
    executable: bool
    review_id: uuid.UUID | None = None


class RunEvaluationRequest(BaseModel):
    input: EvaluationInput
    metrics: list[EvaluationMetric] = Field(default_factory=lambda: list(EvaluationMetric))
    weights: dict[EvaluationMetric, float] = Field(default_factory=dict)
    pass_threshold: float = Field(default=0.70, ge=0.0, le=1.0)
    evaluator_version: str = Field(default="v10", min_length=1, max_length=50)


class RunEvaluationResponse(BaseModel):
    run_id: uuid.UUID
    evaluation_run_id: uuid.UUID
    aggregate_score: float
    passed: bool
    metrics: dict[str, float]
