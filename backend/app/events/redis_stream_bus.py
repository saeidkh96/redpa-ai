from __future__ import annotations

import json
import os
from typing import Any

from redis.asyncio import Redis

from app.events.contracts import EventEnvelope, EventPublishResult


class RedisStreamEventBus:
    def __init__(
        self,
        *,
        redis_url: str | None = None,
        stream: str | None = None,
    ) -> None:
        self.redis_url = (
            redis_url
            or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        )
        self.stream = (
            stream
            or os.getenv("EVENT_STREAM_NAME", "redpa:events")
        )

    async def publish(
        self,
        event: EventEnvelope,
    ) -> EventPublishResult:
        client = Redis.from_url(
            self.redis_url,
            decode_responses=True,
        )

        fields: dict[str, Any] = {
            "event_id": str(event.event_id),
            "event_type": event.event_type,
            "aggregate_type": event.aggregate_type,
            "aggregate_id": event.aggregate_id,
            "occurred_at": event.occurred_at.isoformat(),
            "payload": json.dumps(
                event.payload,
                separators=(",", ":"),
                default=str,
            ),
            "metadata": json.dumps(
                event.metadata,
                separators=(",", ":"),
                default=str,
            ),
            "tenant_id": (
                str(event.tenant_id)
                if event.tenant_id is not None
                else ""
            ),
            "correlation_id": event.correlation_id or "",
            "causation_id": event.causation_id or "",
        }

        try:
            message_id = await client.xadd(
                self.stream,
                fields,
            )
        finally:
            await client.aclose()

        return EventPublishResult(
            event_id=event.event_id,
            stream=self.stream,
            message_id=str(message_id),
        )
