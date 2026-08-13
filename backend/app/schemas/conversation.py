import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        examples=["Research about agentic AI"],
    )


class ConversationUpdate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=255,
        examples=["BMW Agentic AI Research"],
    )


class ConversationResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    items: list[ConversationResponse]
    total: int
    limit: int
    offset: int