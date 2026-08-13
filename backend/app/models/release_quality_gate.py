from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ReleaseQualityGateRecord(Base):
    __tablename__ = "release_quality_gates"
    __table_args__ = (
        Index("ix_release_quality_gates_created_at", "created_at"),
        Index("ix_release_quality_gates_candidate_run_id", "candidate_run_id"),
        Index("ix_release_quality_gates_decision_created_at", "decision", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    baseline_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    candidate_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    release_label: Mapped[str | None] = mapped_column(String(length=200), nullable=True)
    decision: Mapped[str] = mapped_column(String(length=16), nullable=False)
    reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    baseline_score: Mapped[float] = mapped_column(Float, nullable=False)
    candidate_score: Mapped[float] = mapped_column(Float, nullable=False)
    aggregate_delta: Mapped[float] = mapped_column(Float, nullable=False)
    regression_detected: Mapped[bool] = mapped_column(Boolean, nullable=False)
    regressed_metrics: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    max_aggregate_drop: Mapped[float] = mapped_column(Float, nullable=False)
    max_metric_drop: Mapped[float] = mapped_column(Float, nullable=False)
    minimum_candidate_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    require_candidate_pass: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    gate_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
