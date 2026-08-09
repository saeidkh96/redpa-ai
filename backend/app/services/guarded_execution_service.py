from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.guardrails.contracts import GuardrailEvaluation
from app.mcp.schemas import MCPToolCallResult
from app.services.mcp_service import MCPService
from app.services.policy_enforcement_service import (
    PolicyEnforcementService,
)
from app.services.tool_service import ToolService
from app.tools.schemas import ToolExecutionResult


@dataclass(frozen=True, slots=True)
class GuardedExecutionResult:
    evaluation: GuardrailEvaluation
    review_id: uuid.UUID | None
    executed: bool
    result: ToolExecutionResult | MCPToolCallResult | None


class GuardedExecutionService:
    """Single policy boundary for internal and MCP tool execution."""

    def __init__(
        self,
        *,
        enforcement: PolicyEnforcementService | None = None,
    ) -> None:
        self.enforcement = enforcement or PolicyEnforcementService()

    async def execute_internal(
        self,
        *,
        session: AsyncSession,
        user_id: uuid.UUID,
        tool_name: str,
        arguments: dict[str, Any],
        conversation_id: uuid.UUID | None = None,
        message_id: uuid.UUID | None = None,
        workflow_id: str | None = None,
        request_content: str | None = None,
        approval_granted: bool = False,
    ) -> GuardedExecutionResult:
        enforcement = await self.enforcement.enforce(
            session=session,
            boundary="internal_tool",
            action=tool_name,
            resource="tool",
            arguments=arguments,
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            workflow_id=workflow_id,
            request_content=request_content,
            approval_granted=approval_granted,
        )

        if not enforcement.executable:
            return GuardedExecutionResult(
                evaluation=enforcement.evaluation,
                review_id=(
                    enforcement.review.id
                    if enforcement.review
                    else None
                ),
                executed=False,
                result=None,
            )

        result = await ToolService.execute(
            tool_name=tool_name,
            arguments=arguments,
        )
        return GuardedExecutionResult(
            evaluation=enforcement.evaluation,
            review_id=None,
            executed=True,
            result=result,
        )

    async def execute_mcp(
        self,
        *,
        session: AsyncSession,
        user_id: uuid.UUID,
        qualified_name: str,
        arguments: dict[str, Any],
        conversation_id: uuid.UUID | None = None,
        message_id: uuid.UUID | None = None,
        workflow_id: str | None = None,
        request_content: str | None = None,
        approval_granted: bool = False,
    ) -> GuardedExecutionResult:
        enforcement = await self.enforcement.enforce(
            session=session,
            boundary="mcp",
            action=qualified_name,
            resource="mcp_tool",
            arguments=arguments,
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            workflow_id=workflow_id,
            request_content=request_content,
            approval_granted=approval_granted,
        )

        if not enforcement.executable:
            return GuardedExecutionResult(
                evaluation=enforcement.evaluation,
                review_id=(
                    enforcement.review.id
                    if enforcement.review
                    else None
                ),
                executed=False,
                result=None,
            )

        result = await MCPService.call_qualified_tool(
            qualified_name=qualified_name,
            arguments=arguments,
            approval_granted=approval_granted,
        )
        return GuardedExecutionResult(
            evaluation=enforcement.evaluation,
            review_id=None,
            executed=True,
            result=result,
        )


guarded_execution_service = GuardedExecutionService()
