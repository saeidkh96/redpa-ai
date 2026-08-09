from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class EvaluationRunTelemetry(BaseModel):
    total: int
    completed: int
    failed: int
    active: int
    success_rate: float
    average_aggregate_score: float


class EvaluationMetricTelemetry(BaseModel):
    count: int
    passed: int
    failed: int
    average_score: float


class BenchmarkTelemetry(BaseModel):
    runs: int
    cases: int
    passed_cases: int
    pass_rate: float


class EvaluationObservabilityResponse(BaseModel):
    runs: EvaluationRunTelemetry
    metrics: dict[str, EvaluationMetricTelemetry]
    benchmarks: BenchmarkTelemetry
