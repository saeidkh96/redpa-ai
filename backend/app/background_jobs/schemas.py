from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field

class BackgroundJobCreate(BaseModel):
    job_type: str = Field(min_length=1, max_length=100)
    payload: dict[str, Any] = Field(default_factory=dict)
    max_attempts: int = Field(default=3, ge=1, le=20)
    delay_seconds: int = Field(default=0, ge=0, le=604800)

class BackgroundJobRecord(BaseModel):
    id: UUID
    job_type: str
    payload: dict[str, Any]
    status: str
    attempt_count: int
    max_attempts: int
    available_at: datetime
    locked_at: datetime | None
    completed_at: datetime | None
    failed_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime
