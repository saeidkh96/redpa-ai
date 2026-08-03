from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MultiAgentSubtask(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    id: str = Field(
        min_length=1,
        max_length=100,
    )
    instruction: str = Field(
        min_length=1,
        max_length=10_000,
    )


class MultiAgentRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    request: str = Field(
        min_length=1,
        max_length=30_000,
    )
    subtasks: list[MultiAgentSubtask] = Field(
        default_factory=list,
        max_length=20,
    )
    max_parallelism: int = Field(
        default=4,
        ge=1,
        le=10,
    )
    timeout_seconds: float = Field(
        default=90.0,
        ge=1.0,
        le=600.0,
    )
    approval_granted: bool = False


class MultiAgentExecutionItem(BaseModel):
    subtask_id: str
    instruction: str
    remote_agent: str | None
    selected_skill: str | None
    success: bool
    response: str | None
    task_id: str | None
    context_id: str | None
    execution_time_ms: float
    error: str | None


class MultiAgentResponse(BaseModel):
    success: bool
    approval_required: bool
    review_reason: str | None
    request: str
    results: list[MultiAgentExecutionItem]
    aggregated_response: str
    total_subtasks: int
    successful_subtasks: int
    failed_subtasks: int
    execution_time_ms: float
    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )
