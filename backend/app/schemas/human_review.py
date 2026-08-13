import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.human_review import HumanReviewStatus


class HumanReviewDecisionRequest(BaseModel):
    feedback: str | None = Field(
        default=None,
        max_length=5000,
        examples=[
            "The requested action was reviewed and approved.",
        ],
    )


class HumanReviewResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID
    conversation_id: uuid.UUID
    user_id: uuid.UUID
    message_id: uuid.UUID | None

    status: HumanReviewStatus
    reason: str

    requested_action: str | None
    request_content: str | None
    action_payload: dict[str, Any] | None

    reviewer_feedback: str | None
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None

    created_at: datetime
    updated_at: datetime


class HumanReviewListResponse(BaseModel):
    items: list[HumanReviewResponse]
    total: int
    limit: int
    offset: int