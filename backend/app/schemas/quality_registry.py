from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.benchmark import BenchmarkCaseRequest, BenchmarkRunResponse
from app.schemas.reliability_validation import ReliabilityScorecardResponse


class BenchmarkSuiteCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    cases: list[BenchmarkCaseRequest] = Field(min_length=1)
    pass_threshold: float = Field(default=0.70, ge=0.0, le=1.0)
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class BenchmarkSuiteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    cases: list[dict[str, Any]]
    pass_threshold: float
    enabled: bool
    suite_metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class BenchmarkSuiteListResponse(BaseModel):
    items: list[BenchmarkSuiteResponse]
    total: int
    limit: int
    offset: int


class BenchmarkSuiteRunRequest(BaseModel):
    agent_id: str | None = Field(default=None, max_length=150)
    model_name: str | None = Field(default=None, max_length=200)
    run_name: str | None = Field(default=None, max_length=200)


class BenchmarkSuiteRunResponse(BaseModel):
    suite_id: uuid.UUID
    benchmark: BenchmarkRunResponse


class ReliabilitySnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    overall_score: float
    healthy_providers: int
    degraded_providers: int
    unavailable_providers: int
    providers: list[dict[str, Any]]
    created_at: datetime


class ReliabilityHistoryResponse(BaseModel):
    items: list[ReliabilitySnapshotResponse]
    total: int
    limit: int
    offset: int


class ReliabilityCaptureResponse(BaseModel):
    snapshot: ReliabilitySnapshotResponse
    scorecard: ReliabilityScorecardResponse


class ReleaseCandidateReportResponse(BaseModel):
    candidate_run_id: uuid.UUID
    candidate_name: str
    candidate_score: float
    candidate_threshold: float
    latest_gate_id: uuid.UUID | None
    latest_gate_decision: str | None
    latest_gate_reasons: list[str]
    latest_gate_created_at: datetime | None
    latest_benchmark_id: uuid.UUID | None
    latest_benchmark_score: float | None
    latest_benchmark_pass_rate: float | None
    reliability_score: float | None
    reliability_snapshot_at: datetime | None
    promotion_ready: bool
    blockers: list[str]
