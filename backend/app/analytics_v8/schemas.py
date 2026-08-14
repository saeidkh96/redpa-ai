from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Aggregation = Literal["sum", "avg", "weighted_avg", "count", "min", "max"]


class AnalyticsEventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    metric: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.-]+$")
    value: float
    weight: float = Field(default=1.0, ge=0.0)
    dimensions: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime | None = None

    @field_validator("dimensions")
    @classmethod
    def validate_dimensions(cls, value: dict[str, str]) -> dict[str, str]:
        if len(value) > 20:
            raise ValueError("At most 20 dimensions are allowed per analytics event.")
        for key, item in value.items():
            if not key or len(key) > 64 or not key.replace("_", "").replace("-", "").isalnum():
                raise ValueError(f"Invalid dimension key: {key!r}")
            if len(item) > 200:
                raise ValueError(f"Dimension value is too long: {key!r}")
        return value


class AnalyticsEventBatch(BaseModel):
    items: list[AnalyticsEventCreate] = Field(min_length=1, max_length=1000)


class KPIQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    metric: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.-]+$")
    aggregation: Aggregation = "sum"
    group_by: list[str] = Field(default_factory=list, max_length=5)
    filters: dict[str, str] = Field(default_factory=dict)
    start_at: datetime | None = None
    end_at: datetime | None = None

    @field_validator("group_by")
    @classmethod
    def validate_group_by(cls, value: list[str]) -> list[str]:
        for key in value:
            if not key or len(key) > 64 or not key.replace("_", "").replace("-", "").isalnum():
                raise ValueError(f"Invalid group-by dimension: {key!r}")
        return value


class KPIGroup(BaseModel):
    dimensions: dict[str, str]
    value: float
    event_count: int
    total_weight: float


class KPIQueryResponse(BaseModel):
    metric: str
    aggregation: Aggregation
    groups: list[KPIGroup]
    total_groups: int


class AnalyticsCatalog(BaseModel):
    metrics: list[str]
    dimensions: list[str]
