from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.governance_v10 import AgentRun, AgentRunEvent


class AgentRunNotFoundError(Exception):
    """Raised when a V10 governed agent run cannot be found."""


class AgentRunRepository:
    @staticmethod
    async def create(*, session: AsyncSession, run: AgentRun) -> AgentRun:
        session.add(run)
        await session.commit()
        return await AgentRunRepository.get(session=session, run_id=run.id)

    @staticmethod
    async def get(*, session: AsyncSession, run_id: uuid.UUID, user_id: uuid.UUID | None = None) -> AgentRun:
        filters = [AgentRun.id == run_id]
        if user_id is not None:
            filters.append(AgentRun.user_id == user_id)
        result = await session.execute(
            select(AgentRun).where(*filters).options(selectinload(AgentRun.events))
        )
        run = result.scalar_one_or_none()
        if run is None:
            raise AgentRunNotFoundError("Agent run not found.")
        return run

    @staticmethod
    async def find_by_workflow(
        *, session: AsyncSession, workflow_id: str, user_id: uuid.UUID
    ) -> AgentRun | None:
        result = await session.execute(
            select(AgentRun)
            .where(AgentRun.workflow_id == workflow_id, AgentRun.user_id == user_id)
            .options(selectinload(AgentRun.events))
            .order_by(AgentRun.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list(*, session: AsyncSession, user_id: uuid.UUID, limit: int, offset: int, agent_id: str | None = None, status: str | None = None) -> tuple[list[AgentRun], int]:
        filters = [AgentRun.user_id == user_id]
        if agent_id:
            filters.append(AgentRun.agent_id == agent_id)
        if status:
            filters.append(AgentRun.status == status)
        query = (
            select(AgentRun)
            .where(*filters)
            .options(selectinload(AgentRun.events))
            .order_by(AgentRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        count_query = select(func.count()).select_from(AgentRun).where(*filters)
        result = await session.execute(query)
        count = await session.execute(count_query)
        return list(result.scalars().unique().all()), count.scalar_one()

    @staticmethod
    async def add_event(*, session: AsyncSession, event: AgentRunEvent, commit: bool = True) -> AgentRunEvent:
        session.add(event)
        if commit:
            await session.commit()
            await session.refresh(event)
        else:
            await session.flush()
        return event
