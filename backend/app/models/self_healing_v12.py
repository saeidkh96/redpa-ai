from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Index, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class SelfHealingCheckpoint(Base):
    __tablename__ = "self_healing_checkpoints"

    __table_args__ = (
        Index(
            "ix_self_healing_checkpoint_stage_updated",
            "stage",
            "updated_at",
        ),
        Index(
            "ix_self_healing_checkpoint_failed_agent",
            "failed_agent_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    idempotency_key: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
        index=True,
    )

    stage: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    failed_agent_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    replacement_agent_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    workflow_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
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