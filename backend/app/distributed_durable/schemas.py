from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.distributed_multi.schemas import (
    DistributedSubtask,
    DistributedSubtaskResult,
)


class DurableWorkflowCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    request: str = Field(
        min_length=1,
        max_length=30_000,
    )
    subtasks: list[DistributedSubtask] = Field(
        default_factory=list,
        max_length=20,
    )
    max_parallelism: int = Field(
        default=4,
        ge=1,
        le=10,
    )
    timeout_seconds: float = Field(
        default=120.0,
        ge=1.0,
        le=900.0,
    )
    approval_granted: bool = False


class DurableWorkflowResume(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    approval_granted: bool = False
    retry_failed: bool = True
    retry_running: bool = True


class DurableSubtaskRecord(BaseModel):
    id: UUID
    workflow_id: UUID
    subtask_key: str
    instruction: str
    status: str
    remote_agent: str | None
    selected_skill: str | None
    response: str | None
    task_id: str | None
    context_id: str | None
    execution_time_ms: float
    error: str | None
    attempt_count: int
    created_at: datetime
    updated_at: datetime


class DurableWorkflowRecord(BaseModel):
    id: UUID
    request: str
    status: str
    approval_required: bool
    approval_granted: bool
    review_reason: str | None
    max_parallelism: int
    timeout_seconds: float
    aggregated_response: str | None
    successful_subtasks: int
    failed_subtasks: int
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    subtasks: list[DurableSubtaskRecord] = Field(
        default_factory=list,
    )


class DurableWorkflowExecutionResponse(BaseModel):
    workflow: DurableWorkflowRecord
    resumed: bool = False
    executed_subtasks: list[DistributedSubtaskResult] = Field(
        default_factory=list,
    )
