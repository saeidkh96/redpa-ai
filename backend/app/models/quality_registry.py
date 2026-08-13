from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class BenchmarkSuiteRecord(Base):
    __tablename__ = "benchmark_suites"
    __table_args__ = (
        Index("ix_benchmark_suites_name", "name"),
        Index("ix_benchmark_suites_enabled", "enabled"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(length=200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cases: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    pass_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.70)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    suite_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class ReliabilitySnapshotRecord(Base):
    __tablename__ = "reliability_snapshots"
    __table_args__ = (Index("ix_reliability_snapshots_created_at", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    healthy_providers: Mapped[int] = mapped_column(Integer, nullable=False)
    degraded_providers: Mapped[int] = mapped_column(Integer, nullable=False)
    unavailable_providers: Mapped[int] = mapped_column(Integer, nullable=False)
    providers: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
