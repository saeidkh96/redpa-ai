from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.contracts import EventEnvelope, OutboxStatus
from app.models.event_outbox import EventOutbox


class EventOutboxService:
    @staticmethod
    async def enqueue(
        *,
        session: AsyncSession,
        event: EventEnvelope,
        commit: bool = True,
    ) -> EventOutbox:
        row = EventOutbox(
            id=event.event_id,
            tenant_id=event.tenant_id,
            event_type=event.event_type,
            aggregate_type=event.aggregate_type,
            aggregate_id=event.aggregate_id,
            payload=event.payload,
            event_metadata=event.metadata,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            status=OutboxStatus.PENDING.value,
            attempts=0,
        )
        session.add(row)

        if commit:
            await session.commit()
            await session.refresh(row)
        else:
            await session.flush()

        return row

    @staticmethod
    async def pending(
        *,
        session: AsyncSession,
        limit: int = 100,
    ) -> list[EventOutbox]:
        result = await session.execute(
            select(EventOutbox)
            .where(
                EventOutbox.status.in_(
                    [
                        OutboxStatus.PENDING.value,
                        OutboxStatus.FAILED.value,
                    ]
                )
            )
            .order_by(EventOutbox.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def recent(
        *,
        session: AsyncSession,
        limit: int = 100,
    ) -> list[EventOutbox]:
        result = await session.execute(
            select(EventOutbox)
            .order_by(EventOutbox.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def mark_published(
        *,
        session: AsyncSession,
        row: EventOutbox,
        commit: bool = False,
    ) -> None:
        row.status = OutboxStatus.PUBLISHED.value
        row.attempts += 1
        row.last_error = None
        row.published_at = datetime.now(timezone.utc)

        if commit:
            await session.commit()
        else:
            await session.flush()

    @staticmethod
    async def mark_failed(
        *,
        session: AsyncSession,
        row: EventOutbox,
        error: str,
        commit: bool = False,
    ) -> None:
        row.status = OutboxStatus.FAILED.value
        row.attempts += 1
        row.last_error = error[:4000]

        if commit:
            await session.commit()
        else:
            await session.flush()
