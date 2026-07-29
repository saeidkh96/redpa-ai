from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentSource, DocumentStatus


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    conversation_id: UUID | None

    filename: str
    mime_type: str
    size_bytes: int

    status: DocumentStatus
    source: DocumentSource

    storage_path: str | None
    error_message: str | None

    created_at: datetime
    updated_at: datetime