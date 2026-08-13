from __future__ import annotations

from app.model_gateway.contracts import LLMProviderHealth
from app.schemas.reliability_validation import FailureSimulationRequest
from app.services.reliability_validation_service import ReliabilityValidationService


def test_reliability_scorecard_marks_healthy_provider():
    result = ReliabilityValidationService.scorecard(
        health=[
            LLMProviderHealth(
                provider="primary",
                available=True,
                models=("model-a",),
            )
        ],
        circuits={
            "primary": {
                "state": "closed",
                "failures": 0,
                "failure_threshold": 3,
            }
        },
    )
    assert result.overall_score == 1.0
    assert result.healthy_providers == 1
    assert result.providers[0].status == "healthy"


def test_reliability_scorecard_marks_open_circuit_unavailable():
    result = ReliabilityValidationService.scorecard(
        health=[
            LLMProviderHealth(
                provider="primary",
                available=True,
                models=("model-a",),
            )
        ],
        circuits={
            "primary": {
                "state": "open",
                "failures": 3,
                "failure_threshold": 3,
            }
        },
    )
    assert result.unavailable_providers == 1
    assert result.providers[0].score < 0.40


def test_failure_simulation_recovers_on_primary_retry():
    result = ReliabilityValidationService.simulate(
        FailureSimulationRequest(
            primary_failures=1,
            retry_attempts=2,
            fallback_available=True,
        )
    )
    assert result.recovered is True
    assert result.fallback_attempted is False
    assert result.expected_outcome == "primary_recovered"


def test_failure_simulation_validates_fallback_recovery():
    result = ReliabilityValidationService.simulate(
        FailureSimulationRequest(
            primary_failures=2,
            retry_attempts=2,
            fallback_available=True,
        )
    )
    assert result.recovered is True
    assert result.fallback_attempted is True
    assert result.expected_outcome == "fallback_recovered"


def test_non_retryable_failure_does_not_fallback():
    result = ReliabilityValidationService.simulate(
        FailureSimulationRequest(
            primary_failures=2,
            retry_attempts=3,
            fallback_available=True,
            primary_retryable=False,
        )
    )
    assert result.recovered is False
    assert result.fallback_attempted is False
    assert result.expected_outcome == "failed"
