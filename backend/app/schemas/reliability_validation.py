from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ReliabilityProviderScore(BaseModel):
    provider: str
    available: bool
    circuit_state: str
    failures: int
    failure_threshold: int
    score: float
    status: Literal["healthy", "degraded", "unavailable"]


class ReliabilityScorecardResponse(BaseModel):
    overall_score: float
    healthy_providers: int
    degraded_providers: int
    unavailable_providers: int
    providers: list[ReliabilityProviderScore]


class FailureSimulationRequest(BaseModel):
    primary_failures: int = Field(default=1, ge=1, le=10)
    retry_attempts: int = Field(default=2, ge=1, le=10)
    fallback_available: bool = True
    primary_retryable: bool = True


class FailureSimulationResponse(BaseModel):
    primary_attempts: int
    fallback_attempted: bool
    recovered: bool
    expected_outcome: Literal["primary_recovered", "fallback_recovered", "failed"]
    events: list[str]
