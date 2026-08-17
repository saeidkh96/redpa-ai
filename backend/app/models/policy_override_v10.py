from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class PolicyOverrideV10(Base):
    __tablename__ = "policy_overrides_v10"
    __table_args__ = (
        UniqueConstraint("user_id", "boundary", "action", name="uq_policy_override_v10_user_boundary_action"),
        Index("ix_policy_overrides_v10_user_enabled", "user_id", "enabled"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    boundary: Mapped[str] = mapped_column(String(50), nullable=False, default="tool")
    action: Mapped[str] = mapped_column(String(300), nullable=False)
    resource: Mapped[str | None] = mapped_column(String(200), nullable=True)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    risk: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
