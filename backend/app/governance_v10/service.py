from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.governance_v10.repository import AgentRunRepository
from app.governance_v10.schemas import (
    AgentRunCreate,
    AgentRunEventCreate,
    AgentRunUpdate,
    RunEvaluationRequest,
    RunEvaluationResponse,
    RunPolicyCheckRequest,
    RunPolicyCheckResponse,
)
from app.models.governance_v10 import AgentRun, AgentRunEvent, AgentRunStatus
from app.observability.context import current_span_id, current_trace_id
from app.schemas.evaluation import EvaluationRequest
from app.services.evaluation_service import EvaluationService
from app.services.policy_enforcement_service import policy_enforcement_service


class InvalidAgentRunTransitionError(Exception):
    """Raised when a governed run attempts an invalid lifecycle transition."""


_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    AgentRunStatus.CREATED.value: {AgentRunStatus.RUNNING.value, AgentRunStatus.BLOCKED.value, AgentRunStatus.FAILED.value},
    AgentRunStatus.RUNNING.value: {AgentRunStatus.COMPLETED.value, AgentRunStatus.BLOCKED.value, AgentRunStatus.FAILED.value},
    AgentRunStatus.BLOCKED.value: {AgentRunStatus.RUNNING.value, AgentRunStatus.FAILED.value},
    AgentRunStatus.COMPLETED.value: set(),
    AgentRunStatus.FAILED.value: set(),
}


class AgentGovernanceService:
    def __init__(self, *, evaluation_service: EvaluationService | None = None) -> None:
        self.evaluation_service = evaluation_service or EvaluationService()

    async def create_run(self, *, session: AsyncSession, user_id: uuid.UUID, payload: AgentRunCreate) -> AgentRun:
        run = AgentRun(
            user_id=user_id,
            agent_id=payload.agent_id,
            workflow_id=payload.workflow_id,
            trace_id=current_trace_id(),
            status=AgentRunStatus.CREATED.value,
            objective=payload.objective,
            model_name=payload.model_name,
            input_payload=payload.input_payload,
            run_metadata=payload.metadata,
        )
        created = await AgentRunRepository.create(session=session, run=run)
        await self._record_event(
            session=session,
            run_id=created.id,
            event_type="run.created",
            stage="governance",
            payload={"agent_id": created.agent_id, "workflow_id": created.workflow_id},
        )
        return await AgentRunRepository.get(session=session, run_id=created.id, user_id=user_id)

    async def update_run(self, *, session: AsyncSession, run_id: uuid.UUID, user_id: uuid.UUID, payload: AgentRunUpdate) -> AgentRun:
        run = await AgentRunRepository.get(session=session, run_id=run_id, user_id=user_id)
        target = payload.status.value
        if target != run.status and target not in _ALLOWED_TRANSITIONS.get(run.status, set()):
            raise InvalidAgentRunTransitionError(f"Invalid agent run transition: {run.status} -> {target}.")

        now = datetime.now(timezone.utc)
        if target == AgentRunStatus.RUNNING.value and run.started_at is None:
            run.started_at = now
        if target in {AgentRunStatus.COMPLETED.value, AgentRunStatus.FAILED.value}:
            run.completed_at = now
        run.status = target
        if payload.output_payload:
            run.output_payload = payload.output_payload
        run.error = payload.error
        await self._record_event(
            session=session,
            run_id=run.id,
            event_type=f"run.{target}",
            stage="lifecycle",
            payload={"error": payload.error} if payload.error else {},
            commit=False,
        )
        await session.commit()
        return await AgentRunRepository.get(session=session, run_id=run.id, user_id=user_id)

    async def add_event(self, *, session: AsyncSession, run_id: uuid.UUID, user_id: uuid.UUID, payload: AgentRunEventCreate) -> AgentRunEvent:
        await AgentRunRepository.get(session=session, run_id=run_id, user_id=user_id)
        return await self._record_event(
            session=session,
            run_id=run_id,
            event_type=payload.event_type,
            stage=payload.stage,
            payload=payload.payload,
        )

    async def resume_run(self, *, session: AsyncSession, run_id: uuid.UUID, user_id: uuid.UUID) -> AgentRun:
        run = await AgentRunRepository.get(session=session, run_id=run_id, user_id=user_id)
        if run.status == AgentRunStatus.RUNNING.value:
            return run
        if run.status != AgentRunStatus.BLOCKED.value:
            raise InvalidAgentRunTransitionError(
                f"Only blocked runs can be resumed; current status is {run.status}."
            )
        return await self.update_run(
            session=session,
            run_id=run_id,
            user_id=user_id,
            payload=AgentRunUpdate(status=AgentRunStatus.RUNNING),
        )

    async def policy_check(self, *, session: AsyncSession, run_id: uuid.UUID, user_id: uuid.UUID, payload: RunPolicyCheckRequest) -> RunPolicyCheckResponse:
        run = await AgentRunRepository.get(session=session, run_id=run_id, user_id=user_id)
        enforcement = await policy_enforcement_service.enforce(
            session=session,
            boundary=payload.boundary,
            action=payload.action,
            arguments=payload.arguments,
            user_id=user_id,
            conversation_id=payload.conversation_id,
            message_id=payload.message_id,
            workflow_id=run.workflow_id,
            resource=payload.resource,
            request_content=payload.request_content,
            approval_granted=payload.approval_granted,
            metadata={**payload.metadata, "agent_id": run.agent_id, "agent_run_id": str(run.id)},
        )
        evaluation = enforcement.evaluation
        await self._record_event(
            session=session,
            run_id=run.id,
            event_type="policy.decision",
            stage="governance",
            payload={
                "decision": evaluation.decision.value,
                "risk": evaluation.risk.value,
                "reason": evaluation.reason,
                "matched_rules": list(evaluation.matched_rules),
                "policy_version": evaluation.policy_version,
                "executable": enforcement.executable,
                "review_id": str(enforcement.review.id) if enforcement.review else None,
            },
        )
        if not enforcement.executable:
            run.status = AgentRunStatus.BLOCKED.value
            await session.commit()
        return RunPolicyCheckResponse(
            run_id=run.id,
            decision=evaluation.decision.value,
            risk=evaluation.risk.value,
            reason=evaluation.reason,
            matched_rules=list(evaluation.matched_rules),
            policy_version=evaluation.policy_version,
            source=evaluation.source,
            executable=enforcement.executable,
            review_id=enforcement.review.id if enforcement.review else None,
        )

    async def evaluate_run(self, *, session: AsyncSession, run_id: uuid.UUID, user_id: uuid.UUID, payload: RunEvaluationRequest) -> RunEvaluationResponse:
        run = await AgentRunRepository.get(session=session, run_id=run_id, user_id=user_id)
        evaluation = await self.evaluation_service.create_and_evaluate(
            session=session,
            request=EvaluationRequest(
                name=f"V10 governed run {run.id}",
                metrics=payload.metrics,
                input=payload.input,
                evaluator_version=payload.evaluator_version,
                source_type="agent_run_v10",
                source_id=str(run.id),
                agent_id=run.agent_id,
                model_name=run.model_name,
                weights=payload.weights,
                pass_threshold=payload.pass_threshold,
                metadata={"agent_run_id": str(run.id), "workflow_id": run.workflow_id},
            ),
        )
        score = float(evaluation.aggregate_score or 0.0)
        run.evaluation_run_id = evaluation.id
        run.evaluation_score = score
        await self._record_event(
            session=session,
            run_id=run.id,
            event_type="evaluation.completed",
            stage="evaluation",
            payload={
                "evaluation_run_id": str(evaluation.id),
                "aggregate_score": score,
                "pass_threshold": evaluation.pass_threshold,
            },
            commit=False,
        )
        await session.commit()
        return RunEvaluationResponse(
            run_id=run.id,
            evaluation_run_id=evaluation.id,
            aggregate_score=score,
            passed=score >= evaluation.pass_threshold,
            metrics={item.metric: item.score for item in evaluation.results},
        )

    async def _record_event(self, *, session: AsyncSession, run_id: uuid.UUID, event_type: str, stage: str | None, payload: dict[str, Any], commit: bool = True) -> AgentRunEvent:
        event = AgentRunEvent(
            run_id=run_id,
            event_type=event_type,
            stage=stage,
            trace_id=current_trace_id(),
            span_id=current_span_id(),
            payload=payload,
        )
        return await AgentRunRepository.add_event(session=session, event=event, commit=commit)
