from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from prometheus_client import Counter, Gauge
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.contracts import OutboxStatus
from app.models.event_outbox import EventOutbox
from app.models.platform_v4_control import PlatformEventDelivery


EVENT_DELIVERY_FAILURES_TOTAL = Counter(
    "redpa_platform_event_delivery_failures_total",
    "v4 event delivery failures.",
    ("consumer",),
)
EVENT_DLQ_TOTAL = Counter(
    "redpa_platform_event_dlq_total",
    "Events moved to the v4 dead-letter queue.",
    ("consumer",),
)
EVENT_REPLAYS_TOTAL = Counter(
    "redpa_platform_event_replays_total",
    "v4 dead-letter event replays.",
    ("consumer",),
)
EVENT_DLQ_SIZE = Gauge(
    "redpa_platform_event_dlq_size",
    "Current number of v4 dead-letter deliveries.",
)


class PlatformEventDeliveryNotFoundError(LookupError):
    pass


class PlatformEventService:
    @staticmethod
    async def create_delivery(
        *,
        session: AsyncSession,
        event_id: uuid.UUID,
        consumer: str,
        max_attempts: int = 5,
        commit: bool = True,
    ) -> PlatformEventDelivery:
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        outbox = await session.get(EventOutbox, event_id)
        if outbox is None:
            raise PlatformEventDeliveryNotFoundError(f"Outbox event not found: {event_id}")

        existing_result = await session.execute(
            select(PlatformEventDelivery).where(
                PlatformEventDelivery.event_id == event_id,
                PlatformEventDelivery.consumer == consumer,
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing is not None:
            return existing

        row = PlatformEventDelivery(
            event_id=event_id,
            tenant_id=outbox.tenant_id,
            consumer=consumer.strip(),
            status="pending",
            max_attempts=max_attempts,
        )
        session.add(row)
        await session.flush()
        if commit:
            await session.commit()
            await session.refresh(row)
        return row

    @staticmethod
    async def get_delivery(
        *,
        session: AsyncSession,
        delivery_id: uuid.UUID,
        lock: bool = False,
    ) -> PlatformEventDelivery:
        query = select(PlatformEventDelivery).where(PlatformEventDelivery.id == delivery_id)
        if lock:
            query = query.with_for_update()
        result = await session.execute(query)
        row = result.scalar_one_or_none()
        if row is None:
            raise PlatformEventDeliveryNotFoundError(str(delivery_id))
        return row

    @classmethod
    async def mark_delivered(
        cls,
        *,
        session: AsyncSession,
        delivery_id: uuid.UUID,
    ) -> PlatformEventDelivery:
        row = await cls.get_delivery(session=session, delivery_id=delivery_id, lock=True)
        row.status = "delivered"
        row.last_error = None
        row.next_retry_at = None
        await session.commit()
        await session.refresh(row)
        return row

    @classmethod
    async def mark_failed(
        cls,
        *,
        session: AsyncSession,
        delivery_id: uuid.UUID,
        error: str,
        base_delay_seconds: int = 5,
    ) -> PlatformEventDelivery:
        row = await cls.get_delivery(session=session, delivery_id=delivery_id, lock=True)
        row.attempts += 1
        row.last_error = error[:4000]
        now = datetime.now(timezone.utc)
        EVENT_DELIVERY_FAILURES_TOTAL.labels(consumer=row.consumer).inc()

        if row.attempts >= row.max_attempts:
            if row.status != "dead_letter":
                EVENT_DLQ_SIZE.inc()
            row.status = "dead_letter"
            row.dead_lettered_at = now
            row.next_retry_at = None
            EVENT_DLQ_TOTAL.labels(consumer=row.consumer).inc()
        else:
            row.status = "retry"
            delay = min(base_delay_seconds * (2 ** (row.attempts - 1)), 3600)
            row.next_retry_at = now + timedelta(seconds=delay)

        await session.commit()
        await session.refresh(row)
        return row

    @classmethod
    async def replay(
        cls,
        *,
        session: AsyncSession,
        delivery_id: uuid.UUID,
    ) -> PlatformEventDelivery:
        row = await cls.get_delivery(session=session, delivery_id=delivery_id, lock=True)
        if row.status != "dead_letter":
            raise ValueError("Only dead-letter deliveries can be replayed.")

        outbox = await session.get(EventOutbox, row.event_id)
        if outbox is None:
            raise PlatformEventDeliveryNotFoundError(f"Outbox event not found: {row.event_id}")

        row.status = "pending"
        row.attempts = 0
        row.last_error = None
        row.next_retry_at = None
        row.dead_lettered_at = None
        row.replay_count += 1

        # Re-queue the original event for the existing Redis Streams publisher.
        outbox.status = OutboxStatus.PENDING.value
        outbox.last_error = None
        outbox.published_at = None

        EVENT_DLQ_SIZE.dec()
        EVENT_REPLAYS_TOTAL.labels(consumer=row.consumer).inc()
        await session.commit()
        await session.refresh(row)
        return row

    @staticmethod
    async def list_dead_letters(
        *,
        session: AsyncSession,
        tenant_id: uuid.UUID | None = None,
        consumer: str | None = None,
        limit: int = 100,
    ) -> list[PlatformEventDelivery]:
        query = select(PlatformEventDelivery).where(PlatformEventDelivery.status == "dead_letter")
        if tenant_id is not None:
            query = query.where(PlatformEventDelivery.tenant_id == tenant_id)
        if consumer:
            query = query.where(PlatformEventDelivery.consumer == consumer)
        result = await session.execute(
            query.order_by(PlatformEventDelivery.dead_lettered_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def retry_due(
        *,
        session: AsyncSession,
        limit: int = 100,
    ) -> list[PlatformEventDelivery]:
        now = datetime.now(timezone.utc)
        result = await session.execute(
            select(PlatformEventDelivery)
            .where(
                PlatformEventDelivery.status == "retry",
                PlatformEventDelivery.next_retry_at <= now,
            )
            .order_by(PlatformEventDelivery.next_retry_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
