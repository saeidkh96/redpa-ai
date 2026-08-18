from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adaptive_governance_v13.schemas import GovernanceSignalCreate, PolicyProposalCreate
from app.models.adaptive_governance_v13 import AdaptiveGovernanceSignal, AdaptivePolicyProposal


class AdaptiveGovernanceRepository:
    @staticmethod
    async def add_signal(
        *,
        session: AsyncSession,
        user_id: UUID,
        payload: GovernanceSignalCreate,
    ) -> AdaptiveGovernanceSignal:
        row = AdaptiveGovernanceSignal(
            user_id=user_id,
            **payload.model_dump(),
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row

    @staticmethod
    async def recent_signals(
        *,
        session: AsyncSession,
        user_id: UUID,
        action: str,
        limit: int,
        agent_id: str | None = None,
        tenant_id: str | None = None,
    ) -> list[AdaptiveGovernanceSignal]:
        stmt = (
            select(AdaptiveGovernanceSignal)
            .where(
                AdaptiveGovernanceSignal.user_id == user_id,
                AdaptiveGovernanceSignal.action == action,
            )
            .order_by(AdaptiveGovernanceSignal.created_at.desc())
            .limit(limit)
        )
        if agent_id:
            stmt = stmt.where(AdaptiveGovernanceSignal.agent_id == agent_id)
        if tenant_id:
            stmt = stmt.where(AdaptiveGovernanceSignal.tenant_id == tenant_id)
        return list((await session.scalars(stmt)).all())

    @staticmethod
    async def next_version(
        *,
        session: AsyncSession,
        user_id: UUID,
        action: str,
    ) -> int:
        current = await session.scalar(
            select(func.max(AdaptivePolicyProposal.version)).where(
                AdaptivePolicyProposal.user_id == user_id,
                AdaptivePolicyProposal.action == action,
            )
        )
        return int(current or 0) + 1

    @classmethod
    async def create_proposal(
        cls,
        *,
        session: AsyncSession,
        user_id: UUID,
        payload: PolicyProposalCreate,
    ) -> AdaptivePolicyProposal:
        version = await cls.next_version(
            session=session,
            user_id=user_id,
            action=payload.action,
        )
        status = "review_required" if payload.recommended_risk in {"HIGH", "CRITICAL"} else "proposed"
        row = AdaptivePolicyProposal(
            user_id=user_id,
            version=version,
            status=status,
            auto_applied=False,
            **payload.model_dump(),
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row

    @staticmethod
    async def get_proposal(
        *,
        session: AsyncSession,
        user_id: UUID,
        proposal_id: UUID,
    ) -> AdaptivePolicyProposal | None:
        return await session.scalar(
            select(AdaptivePolicyProposal).where(
                AdaptivePolicyProposal.id == proposal_id,
                AdaptivePolicyProposal.user_id == user_id,
            )
        )

    @staticmethod
    async def list_proposals(
        *,
        session: AsyncSession,
        user_id: UUID,
        limit: int = 100,
    ) -> list[AdaptivePolicyProposal]:
        return list(
            (
                await session.scalars(
                    select(AdaptivePolicyProposal)
                    .where(AdaptivePolicyProposal.user_id == user_id)
                    .order_by(AdaptivePolicyProposal.created_at.desc())
                    .limit(limit)
                )
            ).all()
        )

    @staticmethod
    async def save(
        *,
        session: AsyncSession,
        row: AdaptivePolicyProposal,
    ) -> AdaptivePolicyProposal:
        row.updated_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(row)
        return row
