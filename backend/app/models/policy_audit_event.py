from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Index, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class PolicyAuditEvent(Base):
    __tablename__ = "policy_audit_events"

    __table_args__ = (
        Index(
            "ix_policy_audit_user_created",
            "user_id",
            "created_at",
        ),
        Index(
            "ix_policy_audit_decision_created",
            "decision",
            "created_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    review_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    boundary: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )
    resource: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    decision: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )
    risk: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    matched_rules: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    policy_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    event_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
