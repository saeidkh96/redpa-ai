import uuid

import pytest

from app.guardrails.contracts import (
    GuardrailDecision,
    GuardrailEvaluation,
    RiskLevel,
)
from app.services.guarded_execution_service import (
    GuardedExecutionService,
)
from app.services.policy_enforcement_service import (
    PolicyEnforcementResult,
)


class StubEnforcement:
    def __init__(self, executable: bool) -> None:
        self.executable = executable

    async def enforce(self, **kwargs):
        return PolicyEnforcementResult(
            evaluation=GuardrailEvaluation(
                decision=(
                    GuardrailDecision.ALLOW
                    if self.executable
                    else GuardrailDecision.DENY
                ),
                risk=(
                    RiskLevel.LOW
                    if self.executable
                    else RiskLevel.CRITICAL
                ),
                reason="test",
                matched_rules=("TEST",),
                policy_version="13.6-test",
            ),
            review=None,
            executable=self.executable,
        )


@pytest.mark.asyncio
async def test_denied_internal_tool_is_not_executed() -> None:
    service = GuardedExecutionService(
        enforcement=StubEnforcement(False)
    )

    result = await service.execute_internal(
        session=object(),
        user_id=uuid.uuid4(),
        tool_name="calculator",
        arguments={"expression": "1+1"},
    )

    assert result.executed is False
    assert result.result is None
