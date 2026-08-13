from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.evaluation_regression import EvaluationRegressionResponse


class ReleaseQualityGateRequest(BaseModel):
    baseline_run_id: uuid.UUID
    candidate_run_id: uuid.UUID
    release_label: str | None = Field(default=None, max_length=200)
    max_aggregate_drop: float = Field(default=0.05, ge=0.0, le=1.0)
    max_metric_drop: float = Field(default=0.10, ge=0.0, le=1.0)
    require_candidate_pass: bool = True
    minimum_candidate_score: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReleaseQualityGateResponse(BaseModel):
    id: uuid.UUID
    decision: Literal["PASS", "FAIL"]
    reasons: list[str]
    release_label: str | None
    regression: EvaluationRegressionResponse
    created_at: datetime


class ReleaseQualityGateHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    baseline_run_id: uuid.UUID
    candidate_run_id: uuid.UUID
    release_label: str | None
    decision: str
    reasons: list[str]
    baseline_score: float
    candidate_score: float
    aggregate_delta: float
    regression_detected: bool
    regressed_metrics: list[str]
    max_aggregate_drop: float
    max_metric_drop: float
    minimum_candidate_score: float | None
    require_candidate_pass: bool
    gate_metadata: dict[str, Any]
    created_at: datetime


class ReleaseQualityGateHistoryResponse(BaseModel):
    items: list[ReleaseQualityGateHistoryItem]
    total: int
    limit: int
    offset: int


class BenchmarkTrendPoint(BaseModel):
    id: uuid.UUID
    name: str
    agent_id: str | None
    model_name: str | None
    aggregate_score: float
    pass_rate: float
    metric_averages: dict[str, float]
    created_at: datetime


class BenchmarkTrendResponse(BaseModel):
    items: list[BenchmarkTrendPoint]
    total: int
    agent_id: str | None = None
    model_name: str | None = None
