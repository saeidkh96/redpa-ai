from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SLOSample(BaseModel):
    latency_ms: float = Field(ge=0.0)
    success: bool


class SLOEvaluateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    samples: list[SLOSample] = Field(min_length=1, max_length=100000)
    availability_target: float = Field(default=0.99, gt=0.0, le=1.0)
    p95_latency_target_ms: float = Field(default=1000.0, gt=0.0)


class SLOEvaluation(BaseModel):
    total_requests: int
    successful_requests: int
    availability: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    availability_target: float
    p95_latency_target_ms: float
    availability_passed: bool
    latency_passed: bool
    decision: Literal["PASS", "FAIL"]


class SLOEvaluator:
    @staticmethod
    def percentile(values: list[float], percentile: float) -> float:
        ordered = sorted(values)
        if not ordered:
            return 0.0
        index = max(0, min(len(ordered) - 1, math.ceil(percentile * len(ordered)) - 1))
        return float(ordered[index])

    @classmethod
    def evaluate(cls, payload: SLOEvaluateRequest) -> SLOEvaluation:
        latencies = [sample.latency_ms for sample in payload.samples]
        successful = sum(1 for sample in payload.samples if sample.success)
        availability = successful / len(payload.samples)
        p95 = cls.percentile(latencies, 0.95)
        availability_passed = availability >= payload.availability_target
        latency_passed = p95 <= payload.p95_latency_target_ms
        return SLOEvaluation(
            total_requests=len(payload.samples), successful_requests=successful,
            availability=round(availability, 6),
            p50_latency_ms=round(cls.percentile(latencies, 0.50), 3),
            p95_latency_ms=round(p95, 3),
            p99_latency_ms=round(cls.percentile(latencies, 0.99), 3),
            availability_target=payload.availability_target,
            p95_latency_target_ms=payload.p95_latency_target_ms,
            availability_passed=availability_passed,
            latency_passed=latency_passed,
            decision="PASS" if availability_passed and latency_passed else "FAIL",
        )
