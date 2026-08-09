import uuid

import pytest

from app.guardrails.contracts import (
    GuardrailDecision,
    GuardrailEvaluation,
    RiskLevel,
)
from app.services.policy_enforcement_service import (
    PolicyEnforcementService,
)


class StubGuardrails:
    def __init__(self, decision: GuardrailDecision) -> None:
        self.decision = decision

    async def evaluate(self, request):
        risk = {
            GuardrailDecision.ALLOW: RiskLevel.LOW,
            GuardrailDecision.REVIEW: RiskLevel.HIGH,
            GuardrailDecision.DENY: RiskLevel.CRITICAL,
        }[self.decision]
        return GuardrailEvaluation(
            decision=self.decision,
            risk=risk,
            reason="test",
            matched_rules=("TEST_RULE",),
            policy_version="13.6-test",
        )


class FakeSession:
    def __init__(self) -> None:
        self.added = []
        self.commits = 0

    def add(self, value):
        self.added.append(value)

    async def flush(self):
        for value in self.added:
            if getattr(value, "id", None) is None:
                value.id = uuid.uuid4()

    async def commit(self):
        self.commits += 1

    async def refresh(self, value):
        return None


@pytest.mark.asyncio
async def test_allow_is_executable() -> None:
    service = PolicyEnforcementService(
        guardrails=StubGuardrails(GuardrailDecision.ALLOW)
    )
    session = FakeSession()

    result = await service.enforce(
        session=session,
        boundary="internal_tool",
        action="calculator",
        arguments={},
        user_id=uuid.uuid4(),
    )

    assert result.executable is True
    assert result.review is None


@pytest.mark.asyncio
async def test_deny_is_not_executable() -> None:
    service = PolicyEnforcementService(
        guardrails=StubGuardrails(GuardrailDecision.DENY)
    )
    session = FakeSession()

    result = await service.enforce(
        session=session,
        boundary="mcp",
        action="drop_database",
        arguments={},
        user_id=uuid.uuid4(),
    )

    assert result.executable is False
    assert result.review is None


@pytest.mark.asyncio
async def test_review_with_approval_becomes_executable() -> None:
    service = PolicyEnforcementService(
        guardrails=StubGuardrails(GuardrailDecision.REVIEW)
    )
    session = FakeSession()

    result = await service.enforce(
        session=session,
        boundary="mcp",
        action="send_email",
        arguments={},
        user_id=uuid.uuid4(),
        approval_granted=True,
    )

    assert result.executable is True
    assert result.review is None
