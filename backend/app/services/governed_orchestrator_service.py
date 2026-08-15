from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.governance_v10.runtime import GovernanceRuntime, bind_runtime, reset_runtime
from app.governance_v10.schemas import AgentRunCreate, AgentRunUpdate, RunEvaluationRequest
from app.governance_v10.service import AgentGovernanceService
from app.models.governance_v10 import AgentRunStatus
from app.models.message import Message
from app.schemas.evaluation import EvaluationInput
from app.schemas.orchestrator import OrchestratorResult
from app.services.orchestrator_service import OrchestratorService


class GovernedOrchestratorService:
    """V10 execution bridge: persist governance around the existing LangGraph runtime."""

    @classmethod
    async def run(cls, *, session: AsyncSession, conversation_id: uuid.UUID,
                  user_id: uuid.UUID, history: list[Message]) -> OrchestratorResult:
        objective = cls._objective(history)
        governance = AgentGovernanceService()
        run = await governance.create_run(
            session=session, user_id=user_id,
            payload=AgentRunCreate(
                agent_id="redpa-orchestrator",
                workflow_id=str(conversation_id),
                objective=objective,
                input_payload={"conversation_id": str(conversation_id)},
                metadata={"integration": "v10_phase2", "runtime": "langgraph"},
            ),
        )
        await governance.update_run(
            session=session, run_id=run.id, user_id=user_id,
            payload=AgentRunUpdate(status=AgentRunStatus.RUNNING),
        )
        token = bind_runtime(GovernanceRuntime(
            session=session, user_id=user_id, run_id=run.id, conversation_id=conversation_id
        ))
        try:
            result = await OrchestratorService.run(
                conversation_id=conversation_id, user_id=user_id, history=history
            )
            await governance.update_run(
                session=session, run_id=run.id, user_id=user_id,
                payload=AgentRunUpdate(
                    status=AgentRunStatus.COMPLETED,
                    output_payload={
                        "route": result.route,
                        "provider": result.provider,
                        "model": result.model,
                        "requires_human_review": result.requires_human_review,
                    },
                ),
            )
            await governance.evaluate_run(
                session=session, run_id=run.id, user_id=user_id,
                payload=RunEvaluationRequest(
                    input=EvaluationInput(
                        request_text=objective,
                        response_text=result.response_content,
                        success=True,
                        actual_route=result.route,
                        actual_tools=[result.selected_tool] if result.selected_tool else [],
                        latency_ms=result.planner_latency_ms,
                        metadata={"provider": result.provider, "model": result.model},
                    ),
                    evaluator_version="v10-phase2",
                ),
            )
            return result
        except Exception as exc:
            await governance.update_run(
                session=session, run_id=run.id, user_id=user_id,
                payload=AgentRunUpdate(
                    status=AgentRunStatus.FAILED,
                    error=f"{type(exc).__name__}: {exc}"[:20000],
                ),
            )
            raise
        finally:
            reset_runtime(token)

    @classmethod
    async def stream(cls, *, session: AsyncSession, conversation_id: uuid.UUID,
                     user_id: uuid.UUID, history: list[Message]) -> AsyncIterator[dict[str, Any]]:
        objective = cls._objective(history)
        governance = AgentGovernanceService()
        run = await governance.create_run(
            session=session, user_id=user_id,
            payload=AgentRunCreate(
                agent_id="redpa-orchestrator", workflow_id=str(conversation_id),
                objective=objective, input_payload={"conversation_id": str(conversation_id)},
                metadata={"integration": "v10_phase2", "streaming": True},
            ),
        )
        await governance.update_run(
            session=session, run_id=run.id, user_id=user_id,
            payload=AgentRunUpdate(status=AgentRunStatus.RUNNING),
        )
        token = bind_runtime(GovernanceRuntime(
            session=session, user_id=user_id, run_id=run.id, conversation_id=conversation_id
        ))
        final_data: dict[str, Any] = {}
        try:
            async for event in OrchestratorService.stream(
                conversation_id=conversation_id, user_id=user_id, history=history
            ):
                if event.get("event") in {"workflow_completed", "workflow_result"}:
                    data = event.get("data")
                    if isinstance(data, dict): final_data.update(data)
                yield event
            await governance.update_run(
                session=session, run_id=run.id, user_id=user_id,
                payload=AgentRunUpdate(status=AgentRunStatus.COMPLETED, output_payload=final_data),
            )
        except Exception as exc:
            await governance.update_run(
                session=session, run_id=run.id, user_id=user_id,
                payload=AgentRunUpdate(status=AgentRunStatus.FAILED, error=f"{type(exc).__name__}: {exc}"[:20000]),
            )
            raise
        finally:
            reset_runtime(token)

    @staticmethod
    def _objective(history: list[Message]) -> str:
        for message in reversed(history):
            role = getattr(message, "role", None)
            role_value = getattr(role, "value", role)
            if role_value == "user":
                content = str(getattr(message, "content", "") or "").strip()
                if content: return content
        return "Execute RedPA agent workflow"
