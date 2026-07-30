from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.conversation import Conversation


class HumanReviewStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class HumanReview(Base):
    __tablename__ = "human_reviews"

    __table_args__ = (
        Index(
            "ix_human_reviews_user_id_status_created_at",
            "user_id",
            "status",
            "created_at",
        ),
        Index(
            "ix_human_reviews_conversation_id_created_at",
            "conversation_id",
            "created_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "conversations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
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

    message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "messages.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(length=50),
        nullable=False,
        default=HumanReviewStatus.PENDING.value,
        index=True,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    requested_action: Mapped[str | None] = mapped_column(
        String(length=100),
        nullable=True,
    )

    request_content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    action_payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    reviewer_feedback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="human_reviews",
    )

    def approve(
        self,
        *,
        reviewer_id: uuid.UUID,
        feedback: str | None = None,
    ) -> None:
        self.status = HumanReviewStatus.APPROVED.value
        self.reviewed_by = reviewer_id
        self.reviewer_feedback = feedback
        self.reviewed_at = datetime.now(timezone.utc)

    def reject(
        self,
        *,
        reviewer_id: uuid.UUID,
        feedback: str | None = None,
    ) -> None:
        self.status = HumanReviewStatus.REJECTED.value
        self.reviewed_by = reviewer_id
        self.reviewer_feedback = feedback
        self.reviewed_at = datetime.now(timezone.utc)

    def cancel(self) -> None:
        self.status = HumanReviewStatus.CANCELLED.value
        self.reviewed_at = datetime.now(timezone.utc)

    @property
    def is_pending(self) -> bool:
        return self.status == HumanReviewStatus.PENDING.value

    @property
    def is_approved(self) -> bool:
        return self.status == HumanReviewStatus.APPROVED.value

    @property
    def is_rejected(self) -> bool:
        return self.status == HumanReviewStatus.REJECTED.value

    def __repr__(self) -> str:
        return (
            f"<HumanReview("
            f"id={self.id}, "
            f"conversation_id={self.conversation_id}, "
            f"user_id={self.user_id}, "
            f"status={self.status!r}"
            f")>"
        )