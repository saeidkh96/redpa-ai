from __future__ import annotations

from app.model_gateway.contracts import LLMProviderHealth
from app.schemas.reliability_validation import (
    FailureSimulationRequest,
    FailureSimulationResponse,
    ReliabilityProviderScore,
    ReliabilityScorecardResponse,
)


class ReliabilityValidationService:
    @staticmethod
    def scorecard(
        *,
        health: list[LLMProviderHealth],
        circuits: dict[str, dict[str, object]],
    ) -> ReliabilityScorecardResponse:
        providers: list[ReliabilityProviderScore] = []
        health_by_name = {item.provider: item for item in health}
        names = sorted(set(health_by_name) | set(circuits))

        for name in names:
            health_item = health_by_name.get(name)
            circuit = circuits.get(name, {})
            available = bool(health_item.available) if health_item else False
            state = str(circuit.get("state", "closed"))
            failures = int(circuit.get("failures", 0))
            threshold = max(1, int(circuit.get("failure_threshold", 3)))

            failure_ratio = min(1.0, failures / threshold)
            score = 1.0
            if not available:
                score -= 0.60
            score -= 0.25 * failure_ratio
            if state == "open":
                score -= 0.40
            elif state == "half_open":
                score -= 0.20
            score = max(0.0, min(1.0, score))

            if not available or state == "open" or score < 0.40:
                status = "unavailable"
            elif state == "half_open" or failures > 0 or score < 0.80:
                status = "degraded"
            else:
                status = "healthy"

            providers.append(
                ReliabilityProviderScore(
                    provider=name,
                    available=available,
                    circuit_state=state,
                    failures=failures,
                    failure_threshold=threshold,
                    score=score,
                    status=status,
                )
            )

        overall = (
            sum(item.score for item in providers) / len(providers)
            if providers else 0.0
        )
        return ReliabilityScorecardResponse(
            overall_score=overall,
            healthy_providers=sum(item.status == "healthy" for item in providers),
            degraded_providers=sum(item.status == "degraded" for item in providers),
            unavailable_providers=sum(item.status == "unavailable" for item in providers),
            providers=providers,
        )

    @staticmethod
    def simulate(request: FailureSimulationRequest) -> FailureSimulationResponse:
        events: list[str] = []
        primary_attempts = min(request.primary_failures, request.retry_attempts)

        for attempt in range(1, primary_attempts + 1):
            events.append(f"primary_attempt_{attempt}:failed")

        if not request.primary_retryable:
            events.append("primary_failure:non_retryable")
            return FailureSimulationResponse(
                primary_attempts=1,
                fallback_attempted=False,
                recovered=False,
                expected_outcome="failed",
                events=events[:2],
            )

        if request.primary_failures < request.retry_attempts:
            events.append(f"primary_attempt_{request.primary_failures + 1}:success")
            return FailureSimulationResponse(
                primary_attempts=request.primary_failures + 1,
                fallback_attempted=False,
                recovered=True,
                expected_outcome="primary_recovered",
                events=events,
            )

        events.append("primary_retry_budget:exhausted")
        if request.fallback_available:
            events.append("fallback_attempt_1:success")
            return FailureSimulationResponse(
                primary_attempts=primary_attempts,
                fallback_attempted=True,
                recovered=True,
                expected_outcome="fallback_recovered",
                events=events,
            )

        events.append("fallback:unavailable")
        return FailureSimulationResponse(
            primary_attempts=primary_attempts,
            fallback_attempted=True,
            recovered=False,
            expected_outcome="failed",
            events=events,
        )
