import uuid

import pytest

from app.events.contracts import EventEnvelope, OutboxStatus
from app.services.event_publisher_service import EventPublisherService


def test_event_envelope_requires_type() -> None:
    with pytest.raises(ValueError):
        EventEnvelope(
            event_type="",
            aggregate_type="conversation",
            aggregate_id="1",
            payload={},
        )


def test_outbox_status_values() -> None:
    assert OutboxStatus.PENDING.value == "pending"
    assert OutboxStatus.PUBLISHED.value == "published"
    assert OutboxStatus.FAILED.value == "failed"


class FakeBus:
    def __init__(self) -> None:
        self.published = []

    async def publish(self, event):
        self.published.append(event)
        from app.events.contracts import EventPublishResult
        return EventPublishResult(
            event_id=event.event_id,
            stream="test",
            message_id="1-0",
        )


def test_event_id_is_stable_uuid() -> None:
    event = EventEnvelope(
        event_type="test.created",
        aggregate_type="test",
        aggregate_id="abc",
        payload={"ok": True},
    )
    assert isinstance(event.event_id, uuid.UUID)


def test_publisher_accepts_event_bus_adapter() -> None:
    service = EventPublisherService(bus=FakeBus())
    assert isinstance(service.bus, FakeBus)
