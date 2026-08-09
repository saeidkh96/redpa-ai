from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class EvaluationRunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class EvaluationMetric(str, enum.Enum):
    TASK_SUCCESS = "task_success"
    ROUTING_ACCURACY = "routing_accuracy"
    TOOL_SELECTION_ACCURACY = "tool_selection_accuracy"
    RESPONSE_RELEVANCE = "response_relevance"
    RAG_FAITHFULNESS = "rag_faithfulness"
    CONTEXT_RELEVANCE = "context_relevance"
    LATENCY = "latency"
    TOKEN_USAGE = "token_usage"
    COST = "cost"


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    __table_args__ = (
        Index("ix_evaluation_runs_status_created_at", "status", "created_at"),
        Index("ix_evaluation_runs_agent_id_created_at", "agent_id", "created_at"),
        Index("ix_evaluation_runs_source_type_source_id", "source_type", "source_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(length=200), nullable=False)
    status: Mapped[str] = mapped_column(String(length=50), nullable=False, default=EvaluationRunStatus.PENDING.value, index=True)
    evaluator_version: Mapped[str] = mapped_column(String(length=50), nullable=False, default="v1")
    source_type: Mapped[str | None] = mapped_column(String(length=100), nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(length=255), nullable=True)
    agent_id: Mapped[str | None] = mapped_column(String(length=150), nullable=True, index=True)
    model_name: Mapped[str | None] = mapped_column(String(length=200), nullable=True)
    aggregate_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    pass_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.70)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    results: Mapped[list["EvaluationResult"]] = relationship(
        "EvaluationResult", back_populates="run", cascade="all, delete-orphan", passive_deletes=True
    )

    def mark_running(self) -> None:
        self.status = EvaluationRunStatus.RUNNING.value
        self.started_at = datetime.now(timezone.utc)
        self.error = None

    def mark_completed(self, aggregate_score: float) -> None:
        self.status = EvaluationRunStatus.COMPLETED.value
        self.aggregate_score = aggregate_score
        self.completed_at = datetime.now(timezone.utc)

    def mark_failed(self, error: str) -> None:
        self.status = EvaluationRunStatus.FAILED.value
        self.error = error
        self.completed_at = datetime.now(timezone.utc)


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"
    __table_args__ = (
        Index("ix_evaluation_results_run_id_metric", "run_id", "metric", unique=True),
        Index("ix_evaluation_results_metric_created_at", "metric", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    metric: Mapped[str] = mapped_column(String(length=100), nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    run: Mapped["EvaluationRun"] = relationship("EvaluationRun", back_populates="results")
