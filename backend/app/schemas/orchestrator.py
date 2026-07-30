from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OrchestratorResult(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    response_content: str = Field(
        min_length=1,
    )

    model: str = Field(
        min_length=1,
    )

    provider: str = Field(
        min_length=1,
    )

    route: str = Field(
        min_length=1,
    )

    planner_reason: str = Field(
        min_length=1,
    )

    usage: dict[str, Any] = Field(
        default_factory=dict,
    )

    requires_human_review: bool = False

    review_status: str | None = None
    review_reason: str | None = None
    review_id: str | None = None

    requested_action: str | None = None
    request_content: str | None = None
    action_payload: dict[str, Any] | None = None

    reviewed_by: str | None = None
    reviewed_at: str | None = None
    reviewer_feedback: str | None = None