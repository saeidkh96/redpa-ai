from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EventCreateRequest(BaseModel):
    event_type: str = Field(min_length=1, max_length=200)
    aggregate_type: str = Field(min_length=1, max_length=120)
    aggregate_id: str = Field(min_length=1, max_length=200)
    tenant_id: uuid.UUID | None = None
    correlation_id: str | None = Field(default=None, max_length=200)
    causation_id: str | None = Field(default=None, max_length=200)
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EventOutboxResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID | None
    event_type: str
    aggregate_type: str
    aggregate_id: str
    payload: dict[str, Any]
    event_metadata: dict[str, Any]
    correlation_id: str | None
    causation_id: str | None
    status: str
    attempts: int
    last_error: str | None
    created_at: datetime
    published_at: datetime | None


class EventFlushResponse(BaseModel):
    inspected: int
    published: int
    failed: int
