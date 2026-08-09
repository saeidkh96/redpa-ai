from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.models.evaluation import EvaluationMetric
from app.schemas.evaluation import EvaluationInput


class BenchmarkCaseRequest(BaseModel):
    id: str = Field(min_length=1, max_length=150)
    name: str = Field(min_length=1, max_length=200)
    input: EvaluationInput
    metrics: list[EvaluationMetric]
    tags: list[str] = Field(default_factory=list)
    weights: dict[EvaluationMetric, float] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_metrics(self) -> "BenchmarkCaseRequest":
        if not self.metrics:
            raise ValueError("At least one metric is required.")
        if len(set(self.metrics)) != len(self.metrics):
            raise ValueError("Benchmark case metrics must be unique.")
        return self


class BenchmarkRunRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    cases: list[BenchmarkCaseRequest] = Field(min_length=1)
    agent_id: str | None = Field(default=None, max_length=150)
    model_name: str | None = Field(default=None, max_length=200)
    pass_threshold: float = Field(default=0.70, ge=0.0, le=1.0)


class BenchmarkCaseResultResponse(BaseModel):
    case_id: str
    case_name: str
    aggregate_score: float
    metric_scores: dict[str, float]
    passed: bool
    tags: list[str]
    metadata: dict[str, Any]


class BenchmarkRunResponse(BaseModel):
    id: str
    name: str
    agent_id: str | None
    model_name: str | None
    created_at: datetime
    case_results: list[BenchmarkCaseResultResponse]
    aggregate_score: float
    pass_rate: float
    metric_averages: dict[str, float]


class BenchmarkComparisonRequest(BaseModel):
    runs: list[BenchmarkRunResponse] = Field(min_length=1)


class BenchmarkComparisonItem(BaseModel):
    rank: int
    benchmark_run_id: str
    name: str
    agent_id: str | None
    model_name: str | None
    aggregate_score: float
    pass_rate: float
    metric_averages: dict[str, float]


class BenchmarkComparisonResponse(BaseModel):
    items: list[BenchmarkComparisonItem]
