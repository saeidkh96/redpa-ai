from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Float, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class BenchmarkRunRecord(Base):
    __tablename__ = "benchmark_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(length=200), nullable=False, index=True)
    agent_id: Mapped[str | None] = mapped_column(String(length=150), nullable=True, index=True)
    model_name: Mapped[str | None] = mapped_column(String(length=200), nullable=True, index=True)
    aggregate_score: Mapped[float] = mapped_column(Float, nullable=False)
    pass_rate: Mapped[float] = mapped_column(Float, nullable=False)
    pass_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.70)
    metric_averages: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False, default=dict)
    case_results: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
