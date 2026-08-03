from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DependencyHealth(BaseModel):
    name: str
    status: str
    latency_ms: float | None = None
    detail: str | None = None
    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    timestamp: datetime
    dependencies: list[DependencyHealth] = Field(
        default_factory=list,
    )
