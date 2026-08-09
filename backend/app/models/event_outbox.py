from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Index, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class EventOutbox(Base):
    __tablename__ = "event_outbox"

    __table_args__ = (
        Index(
            "ix_event_outbox_status_created",
            "status",
            "created_at",
        ),
        Index(
            "ix_event_outbox_tenant_created",
            "tenant_id",
            "created_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )
    aggregate_type: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    aggregate_id: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )
    event_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    correlation_id: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    causation_id: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )
    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
