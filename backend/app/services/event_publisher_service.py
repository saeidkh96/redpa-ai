from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.events.contracts import EventEnvelope
from app.events.redis_stream_bus import RedisStreamEventBus
from app.services.event_outbox_service import EventOutboxService


@dataclass(frozen=True, slots=True)
class OutboxFlushResult:
    inspected: int
    published: int
    failed: int


class EventPublisherService:
    def __init__(
        self,
        *,
        bus: RedisStreamEventBus | None = None,
    ) -> None:
        self.bus = bus or RedisStreamEventBus()

    async def flush(
        self,
        *,
        session: AsyncSession,
        limit: int = 100,
    ) -> OutboxFlushResult:
        rows = await EventOutboxService.pending(
            session=session,
            limit=limit,
        )

        published = 0
        failed = 0

        for row in rows:
            event = EventEnvelope(
                event_id=row.id,
                tenant_id=row.tenant_id,
                event_type=row.event_type,
                aggregate_type=row.aggregate_type,
                aggregate_id=row.aggregate_id,
                payload=row.payload,
                correlation_id=row.correlation_id,
                causation_id=row.causation_id,
                metadata=row.event_metadata,
                occurred_at=row.created_at,
            )

            try:
                await self.bus.publish(event)
                await EventOutboxService.mark_published(
                    session=session,
                    row=row,
                )
                published += 1
            except Exception as exc:
                await EventOutboxService.mark_failed(
                    session=session,
                    row=row,
                    error=str(exc),
                )
                failed += 1

        await session.commit()

        return OutboxFlushResult(
            inspected=len(rows),
            published=published,
            failed=failed,
        )


event_publisher_service = EventPublisherService()
