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
            reason="phase13 security test",
            matched_rules=("PHASE13_SECURITY_TEST",),
            policy_version="13.9-test",
        )


class StubPolicyOverrides:
    async def evaluate(
        self,
        *,
        session,
        user_id,
        boundary,
        action,
        resource,
    ):
        return None


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
async def test_deny_cannot_be_overridden_by_approval_flag() -> None:
    service = PolicyEnforcementService(
        guardrails=StubGuardrails(
            GuardrailDecision.DENY,
        ),
        policy_overrides=StubPolicyOverrides(),
    )

    result = await service.enforce(
        session=FakeSession(),
        boundary="mcp",
        action="drop_database",
        arguments={},
        user_id=uuid.uuid4(),
        approval_granted=True,
    )

    assert result.executable is False
    assert result.evaluation.decision == GuardrailDecision.DENY


@pytest.mark.asyncio
async def test_review_without_conversation_fails_closed() -> None:
    service = PolicyEnforcementService(
        guardrails=StubGuardrails(
            GuardrailDecision.REVIEW,
        ),
        policy_overrides=StubPolicyOverrides(),
    )

    result = await service.enforce(
        session=FakeSession(),
        boundary="mcp",
        action="send_email",
        arguments={},
        user_id=uuid.uuid4(),
        conversation_id=None,
        approval_granted=False,
    )

    assert result.executable is False
    assert result.review is None


@pytest.mark.asyncio
async def test_review_with_explicit_approval_can_continue() -> None:
    service = PolicyEnforcementService(
        guardrails=StubGuardrails(
            GuardrailDecision.REVIEW,
        ),
        policy_overrides=StubPolicyOverrides(),
    )

    result = await service.enforce(
        session=FakeSession(),
        boundary="mcp",
        action="send_email",
        arguments={},
        user_id=uuid.uuid4(),
        approval_granted=True,
    )

    assert result.executable is True
    assert (
        result.evaluation.decision
        == GuardrailDecision.REVIEW
    )