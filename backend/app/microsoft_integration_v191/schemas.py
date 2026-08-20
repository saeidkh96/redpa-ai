from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class MicrosoftApprovalRequest(BaseModel):
    conversation_id: UUID
    message_id: UUID | None = None
    incident_id: UUID | None = None
    agent_run_id: UUID | None = None

    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1)
    severity: Literal["low", "medium", "high", "critical"] = "medium"

    requested_action: str = Field(min_length=1, max_length=100)
    request_content: str | None = None
    callback_url: HttpUrl | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)


class MicrosoftApprovalEnvelope(BaseModel):
    connector: Literal["power-automate"] = "power-automate"
    event_type: Literal[
        "redpa.approval.requested"
    ] = "redpa.approval.requested"

    review_id: UUID
    conversation_id: UUID
    incident_id: UUID | None = None
    agent_run_id: UUID | None = None

    title: str
    summary: str
    severity: str
    requested_action: str

    callback_url: HttpUrl | None = None

    requires_approval: bool = True
    status: Literal["pending"] = "pending"

    metadata: dict[str, Any] = Field(default_factory=dict)


class MicrosoftApprovalDecision(BaseModel):
    decision: Literal["approved", "rejected"]
    feedback: str | None = None

    incident_id: UUID | None = None
    agent_run_id: UUID | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)


class MicrosoftApprovalDecisionResult(BaseModel):
    review_id: UUID
    decision: Literal["approved", "rejected"]
    review_status: str

    agent_run_id: UUID | None = None
    agent_run_status: str | None = None

    resume_allowed: bool
    audit_event_recorded: bool
