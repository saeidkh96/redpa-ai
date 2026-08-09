from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class OutboxStatus(StrEnum):
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class EventEnvelope:
    event_type: str
    aggregate_type: str
    aggregate_id: str
    payload: dict[str, Any]
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    tenant_id: uuid.UUID | None = None
    correlation_id: str | None = None
    causation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.event_type.strip():
            raise ValueError("event_type cannot be empty.")
        if not self.aggregate_type.strip():
            raise ValueError("aggregate_type cannot be empty.")
        if not self.aggregate_id.strip():
            raise ValueError("aggregate_id cannot be empty.")


@dataclass(frozen=True, slots=True)
class EventPublishResult:
    event_id: uuid.UUID
    stream: str
    message_id: str
