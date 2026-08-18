from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class AdaptiveGovernanceSignal(Base):
    __tablename__ = "adaptive_governance_signals"
    __table_args__ = (
        Index("ix_adaptive_governance_signal_action_created", "action", "created_at"),
        Index("ix_adaptive_governance_signal_tenant_created", "tenant_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(150), nullable=False)
    agent_id: Mapped[str | None] = mapped_column(String(150), nullable=True)
    tenant_id: Mapped[str | None] = mapped_column(String(150), nullable=True)
    incident_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    error_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    destructive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    write_access: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    handles_secrets: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    external_network: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class AdaptivePolicyProposal(Base):
    __tablename__ = "adaptive_policy_proposals"
    __table_args__ = (
        Index("ix_adaptive_policy_action_version", "action", "version"),
        Index("ix_adaptive_policy_status_updated", "status", "updated_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(150), nullable=False)
    recommended_decision: Mapped[str] = mapped_column(String(20), nullable=False)
    recommended_risk: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="proposed")
    auto_applied: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tenant_id: Mapped[str | None] = mapped_column(String(150), nullable=True)
    agent_id: Mapped[str | None] = mapped_column(String(150), nullable=True)
    source_evidence: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    previous_state: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    applied_state: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rolled_back_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
