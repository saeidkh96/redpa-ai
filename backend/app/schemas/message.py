import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.message import MessageRole, MessageStatus


class MessageCreate(BaseModel):
    content: str = Field(
        min_length=1,
        max_length=50_000,
        examples=[
            "Research the latest applications of agentic AI in the automotive industry."
        ],
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError("Message content cannot be empty.")

        return cleaned_value


class InternalMessageCreate(BaseModel):
    role: MessageRole
    content: str = Field(
        min_length=1,
        max_length=50_000,
    )
    status: MessageStatus = MessageStatus.COMPLETED
    agent_name: str | None = Field(
        default=None,
        max_length=100,
    )
    tool_name: str | None = Field(
        default=None,
        max_length=100,
    )
    extra_data: dict[str, Any] | None = None


class MessageResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID
    conversation_id: uuid.UUID
    role: MessageRole
    content: str
    status: MessageStatus
    agent_name: str | None
    tool_name: str | None
    extra_data: dict[str, Any] | None
    created_at: datetime


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    total: int
    limit: int
    offset: int