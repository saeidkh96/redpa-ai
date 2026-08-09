import pytest

from app.guardrails.contracts import (
    GuardrailAction,
    GuardrailDecision,
    GuardrailEvaluation,
    RiskLevel,
)


def test_guardrail_action_requires_name() -> None:
    with pytest.raises(ValueError):
        GuardrailAction(action="   ")


def test_guardrail_evaluation_helpers() -> None:
    evaluation = GuardrailEvaluation(
        decision=GuardrailDecision.REVIEW,
        risk=RiskLevel.HIGH,
        reason="approval needed",
    )

    assert evaluation.requires_review
    assert not evaluation.allowed
    assert not evaluation.denied
