from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.evaluation import EvaluationMetric, EvaluationRunStatus


class EvaluationInput(BaseModel):
    request_text: str | None = None
    response_text: str | None = None
    success: bool | None = None
    expected_route: str | None = None
    actual_route: str | None = None
    expected_tools: list[str] = Field(default_factory=list)
    actual_tools: list[str] = Field(default_factory=list)
    contexts: list[str] = Field(default_factory=list)
    claims: list[str] = Field(default_factory=list)
    latency_ms: float | None = Field(default=None, ge=0)
    latency_target_ms: float | None = Field(default=None, gt=0)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    token_budget: int | None = Field(default=None, gt=0)
    cost_usd: float | None = Field(default=None, ge=0)
    cost_budget_usd: float | None = Field(default=None, gt=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def total_tokens(self) -> int | None:
        if self.input_tokens is None and self.output_tokens is None:
            return None
        return (self.input_tokens or 0) + (self.output_tokens or 0)


class EvaluationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    metrics: list[EvaluationMetric] = Field(default_factory=lambda: list(EvaluationMetric))
    input: EvaluationInput
    evaluator_version: str = Field(default="v1", min_length=1, max_length=50)
    source_type: str | None = Field(default=None, max_length=100)
    source_id: str | None = Field(default=None, max_length=255)
    agent_id: str | None = Field(default=None, max_length=150)
    model_name: str | None = Field(default=None, max_length=200)
    weights: dict[EvaluationMetric, float] = Field(default_factory=dict)
    pass_threshold: float = Field(default=0.70, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_metrics_and_weights(self) -> "EvaluationRequest":
        if not self.metrics:
            raise ValueError("At least one evaluation metric is required.")
        if len(set(self.metrics)) != len(self.metrics):
            raise ValueError("Evaluation metrics must be unique.")
        if any(weight <= 0 for weight in self.weights.values()):
            raise ValueError("Metric weights must be greater than zero.")
        return self


class MetricEvaluation(BaseModel):
    metric: EvaluationMetric
    score: float = Field(ge=0.0, le=1.0)
    passed: bool
    weight: float = Field(gt=0)
    details: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class EvaluationResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    run_id: uuid.UUID
    metric: EvaluationMetric
    score: float
    passed: bool
    weight: float
    details: dict[str, Any] | None
    error: str | None
    created_at: datetime


class EvaluationRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    status: EvaluationRunStatus
    evaluator_version: str
    source_type: str | None
    source_id: str | None
    agent_id: str | None
    model_name: str | None
    aggregate_score: float | None
    pass_threshold: float
    metadata_: dict[str, Any] | None
    error: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    results: list[EvaluationResultResponse] = Field(default_factory=list)


class EvaluationRunListResponse(BaseModel):
    items: list[EvaluationRunResponse]
    total: int
    limit: int
    offset: int
