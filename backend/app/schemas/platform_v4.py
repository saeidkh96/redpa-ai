from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PlatformBudgetUpsertRequest(BaseModel):
    monthly_token_limit: int = Field(default=1_000_000, gt=0)
    monthly_cost_limit_usd: float = Field(default=25.0, gt=0)
    allowed_providers: list[str] = Field(default_factory=list)


class PlatformBudgetResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    period_key: str
    monthly_token_limit: int
    monthly_cost_limit_usd: float
    used_tokens: int
    used_cost_usd: float
    allowed_providers: list[str]
    created_at: datetime
    updated_at: datetime


class PlatformUsageResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    request_id: str | None
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    route_reason: str | None
    created_at: datetime


class WorkflowDefinitionCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    version: str = Field(min_length=1, max_length=40)
    definition: dict[str, Any] = Field(default_factory=dict)


class WorkflowDefinitionResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    version: str
    definition: dict[str, Any]
    active: bool
    created_by: uuid.UUID
    created_at: datetime


class WorkflowRunCreateRequest(BaseModel):
    workflow_name: str = Field(min_length=1, max_length=160)
    workflow_version: str = Field(min_length=1, max_length=40)
    definition_id: uuid.UUID | None = None
    input_payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = Field(default=None, max_length=200)


class WorkflowRunResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    definition_id: uuid.UUID | None
    workflow_name: str
    workflow_version: str
    status: str
    current_checkpoint: str | None
    attempts: int
    input_payload: dict[str, Any]
    output_payload: dict[str, Any] | None
    last_error: str | None
    correlation_id: str | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class WorkflowCheckpointCreateRequest(BaseModel):
    checkpoint_key: str = Field(min_length=1, max_length=200)
    state: dict[str, Any] = Field(default_factory=dict)
    reason: str | None = Field(default=None, max_length=500)


class WorkflowCheckpointResponse(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    sequence: int
    checkpoint_key: str
    state: dict[str, Any]
    reason: str | None
    created_at: datetime


class WorkflowTransitionRequest(BaseModel):
    status: str = Field(pattern="^(running|paused|completed|failed|cancelled)$")
    reason: str = Field(min_length=1, max_length=500)
    output_payload: dict[str, Any] | None = None
    error: str | None = Field(default=None, max_length=4000)


class EventDeliveryCreateRequest(BaseModel):
    event_id: uuid.UUID
    consumer: str = Field(min_length=1, max_length=160)
    max_attempts: int = Field(default=5, ge=1, le=100)


class EventDeliveryFailureRequest(BaseModel):
    error: str = Field(min_length=1, max_length=4000)
    base_delay_seconds: int = Field(default=5, ge=1, le=3600)


class EventDeliveryResponse(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    tenant_id: uuid.UUID | None
    consumer: str
    status: str
    attempts: int
    max_attempts: int
    last_error: str | None
    next_retry_at: datetime | None
    dead_lettered_at: datetime | None
    replay_count: int
    created_at: datetime
    updated_at: datetime
