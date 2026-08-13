import enum
import uuid

from sqlalchemy import (
    BigInteger,
    Enum as SAEnum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class DocumentStatus(str, enum.Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class DocumentSource(str, enum.Enum):
    UPLOAD = "upload"
    GITHUB = "github"
    NOTION = "notion"
    CONFLUENCE = "confluence"
    GOOGLE_DRIVE = "google_drive"
    S3 = "s3"


class Document(TimestampMixin, Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "conversations.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    mime_type: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    status: Mapped[DocumentStatus] = mapped_column(
        SAEnum(
            DocumentStatus,
            name="document_status",
            native_enum=False,
            validate_strings=True,
            values_callable=lambda enum_class: [
                member.value
                for member in enum_class
            ],
        ),
        nullable=False,
        default=DocumentStatus.UPLOADING,
        server_default=DocumentStatus.UPLOADING.value,
        index=True,
    )

    source: Mapped[DocumentSource] = mapped_column(
        SAEnum(
            DocumentSource,
            name="document_source",
            native_enum=False,
            validate_strings=True,
            values_callable=lambda enum_class: [
                member.value
                for member in enum_class
            ],
        ),
        nullable=False,
        default=DocumentSource.UPLOAD,
        server_default=DocumentSource.UPLOAD.value,
        index=True,
    )

    storage_path: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<Document("
            f"id={self.id}, "
            f"filename={self.filename!r}, "
            f"status={self.status.value!r}"
            f")>"
        )