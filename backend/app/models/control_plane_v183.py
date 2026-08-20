from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import DateTime, Float, Index, Integer, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base

class AgentExecutionRun(Base):
    __tablename__ = "agent_execution_runs"
    __table_args__ = (Index("ix_agent_execution_status_created", "status", "created_at"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="control-plane")
    primary_agent: Mapped[str] = mapped_column(String(120), nullable=False)
    fallback_agent: Mapped[str|None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    evaluation_score: Mapped[float|None] = mapped_column(Float, nullable=True)
    fallback_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    trace_id: Mapped[str|None] = mapped_column(String(128), nullable=True, index=True)
    evidence: Mapped[dict[str,Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
