from __future__ import annotations

from typing import Any, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class FailoverRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    task: str = Field(min_length=1, max_length=1000)
    capability_query: str = Field(min_length=1, max_length=500)
    failed_agent_id: str = Field(min_length=1, max_length=150)
    workflow_id: str | None = None
    run_id: UUID | None = None
    approval_granted: bool = False
    allow_degraded: bool = True
    idempotency_key: str = Field(min_length=8, max_length=200)
    context: dict[str, Any] = Field(default_factory=dict)

class FailoverResult(BaseModel):
    status: Literal["completed", "blocked", "failed", "duplicate"]
    failed_agent_id: str
    replacement_agent_id: str | None = None
    idempotency_key: str
    duplicate_detected: bool = False
    verification: dict[str, Any] = Field(default_factory=dict)
    evidence: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
