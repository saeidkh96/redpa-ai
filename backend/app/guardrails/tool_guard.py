from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.guardrails.contracts import (
    GuardrailAction,
    GuardrailDecision,
    GuardrailEvaluation,
    GuardrailRequest,
)
from app.guardrails.service import GuardrailService
from app.services.tool_service import ToolService
from app.tools.schemas import ToolExecutionResult


@dataclass(frozen=True, slots=True)
class GuardedToolResult:
    evaluation: GuardrailEvaluation
    execution: ToolExecutionResult | None


class GuardedToolService:
    """Policy-enforced facade over the existing ToolService.

    Phase 13 introduces this facade without replacing ToolService globally.
    Later policy phases can wire MCP/A2A execution through this boundary.
    """

    def __init__(
        self,
        *,
        guardrails: GuardrailService | None = None,
    ) -> None:
        self.guardrails = guardrails or GuardrailService()

    async def execute(
        self,
        *,
        tool_name: str,
        arguments: dict[str, Any],
        agent_id: str | None = None,
        user_id: str | None = None,
        workflow_id: str | None = None,
    ) -> GuardedToolResult:
        evaluation = await self.guardrails.evaluate(
            GuardrailRequest(
                action=GuardrailAction(
                    action=tool_name,
                    resource="tool",
                    arguments=arguments,
                ),
                agent_id=agent_id,
                user_id=user_id,
                workflow_id=workflow_id,
            )
        )

        if evaluation.decision != GuardrailDecision.ALLOW:
            return GuardedToolResult(
                evaluation=evaluation,
                execution=None,
            )

        execution = await ToolService.execute(
            tool_name=tool_name,
            arguments=arguments,
        )

        return GuardedToolResult(
            evaluation=evaluation,
            execution=execution,
        )
