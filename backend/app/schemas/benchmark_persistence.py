from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PersistedBenchmarkRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    agent_id: str | None
    model_name: str | None
    aggregate_score: float
    pass_rate: float
    pass_threshold: float
    metric_averages: dict[str, float]
    case_results: list[dict[str, Any]]
    created_at: datetime


class PersistedBenchmarkRunListResponse(BaseModel):
    items: list[PersistedBenchmarkRunResponse]
    total: int
    limit: int
    offset: int
