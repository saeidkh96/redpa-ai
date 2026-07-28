import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.message import MessageResponse


class ChatRequest(BaseModel):
    conversation_id: uuid.UUID

    content: str = Field(
        min_length=1,
        max_length=50_000,
        examples=[
            "Explain how agentic AI can be used in automotive software development."
        ],
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError("Chat message cannot be empty.")

        return cleaned_value


class ChatResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    conversation_id: uuid.UUID
    user_message: MessageResponse
    assistant_message: MessageResponse
    model: str