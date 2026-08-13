from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field


class RegressionMetricDelta(BaseModel):
    metric: str
    baseline_score: float | None = None
    candidate_score: float | None = None
    delta: float | None = None
    regressed: bool = False


class EvaluationRegressionRequest(BaseModel):
    baseline_run_id: uuid.UUID
    candidate_run_id: uuid.UUID
    max_aggregate_drop: float = Field(default=0.05, ge=0.0, le=1.0)
    max_metric_drop: float = Field(default=0.10, ge=0.0, le=1.0)
    require_candidate_pass: bool = True


class EvaluationRegressionResponse(BaseModel):
    baseline_run_id: uuid.UUID
    candidate_run_id: uuid.UUID
    baseline_score: float
    candidate_score: float
    aggregate_delta: float
    metric_deltas: list[RegressionMetricDelta]
    regressed_metrics: list[str]
    regression_detected: bool


class QualityGateRequest(EvaluationRegressionRequest):
    minimum_candidate_score: float | None = Field(default=None, ge=0.0, le=1.0)


class QualityGateResponse(BaseModel):
    decision: Literal["PASS", "FAIL"]
    reasons: list[str]
    regression: EvaluationRegressionResponse
