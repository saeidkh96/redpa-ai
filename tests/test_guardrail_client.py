import httpx
import pytest

from app.guardrails.client import PolicyServiceClient
from app.guardrails.contracts import (
    GuardrailAction,
    GuardrailDecision,
    GuardrailRequest,
    RiskLevel,
)


@pytest.mark.asyncio
async def test_policy_client_normalizes_response() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/policies/evaluate"
        return httpx.Response(
            200,
            json={
                "decision": "ALLOW",
                "risk": "LOW",
                "reason": "safe",
                "matchedRules": ["READ_ONLY_ALLOW"],
                "policyVersion": "13.3.0",
            },
        )

    client = PolicyServiceClient(
        base_url="http://policy",
        transport=httpx.MockTransport(handler),
    )

    result = await client.evaluate(
        GuardrailRequest(
            action=GuardrailAction(
                action="list_containers",
            ),
        )
    )

    assert result.decision == GuardrailDecision.ALLOW
    assert result.risk == RiskLevel.LOW
    assert result.policy_version == "13.3.0"
