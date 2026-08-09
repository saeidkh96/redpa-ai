import pytest

from app.guardrails.client import PolicyServiceClient
from app.guardrails.contracts import (
    GuardrailAction,
    GuardrailDecision,
    GuardrailRequest,
)
from app.guardrails.service import GuardrailService


class BrokenClient(PolicyServiceClient):
    async def evaluate(self, request):
        from app.guardrails.client import PolicyServiceError
        raise PolicyServiceError("offline")


@pytest.mark.asyncio
async def test_policy_failure_fails_closed_to_review() -> None:
    service = GuardrailService(client=BrokenClient())

    result = await service.evaluate(
        GuardrailRequest(
            action=GuardrailAction(
                action="send_email",
            ),
        )
    )

    assert result.decision == GuardrailDecision.REVIEW
    assert "POLICY_SERVICE_FAIL_CLOSED" in result.matched_rules
