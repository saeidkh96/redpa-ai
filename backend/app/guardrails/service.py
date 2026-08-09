from __future__ import annotations

from app.guardrails.client import (
    PolicyServiceClient,
    PolicyServiceError,
)
from app.guardrails.contracts import (
    GuardrailDecision,
    GuardrailEvaluation,
    GuardrailRequest,
    RiskLevel,
)


class GuardrailService:
    """Application service around the external policy boundary.

    Failure mode is deliberately conservative: if policy evaluation is
    unavailable, the action is routed to human review instead of being
    automatically executed.
    """

    def __init__(
        self,
        *,
        client: PolicyServiceClient | None = None,
    ) -> None:
        self.client = client or PolicyServiceClient()

    async def evaluate(
        self,
        request: GuardrailRequest,
    ) -> GuardrailEvaluation:
        try:
            return await self.client.evaluate(request)
        except PolicyServiceError as exc:
            return GuardrailEvaluation(
                decision=GuardrailDecision.REVIEW,
                risk=RiskLevel.HIGH,
                reason=(
                    "Policy service unavailable; fail-closed to "
                    f"human review. {exc}"
                ),
                matched_rules=("POLICY_SERVICE_FAIL_CLOSED",),
                policy_version="fallback",
                source="redpa-fallback",
            )

    async def healthy(self) -> bool:
        return await self.client.health()


guardrail_service = GuardrailService()
