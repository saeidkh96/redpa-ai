from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.guardrails.contracts import (
    GuardrailAction,
    GuardrailDecision,
    GuardrailEvaluation,
    GuardrailRequest,
)
from app.guardrails.service import GuardrailService
from app.models.human_review import HumanReview
from app.monitoring.policy_metrics import (
    POLICY_ENFORCEMENT_TOTAL,
    POLICY_EVALUATIONS_TOTAL,
    POLICY_EVALUATION_DURATION_SECONDS,
    POLICY_REVIEW_CREATED_TOTAL,
)
from app.services.human_review_service import HumanReviewService
from app.services.policy_audit_service import PolicyAuditService


@dataclass(frozen=True, slots=True)
class PolicyEnforcementResult:
    evaluation: GuardrailEvaluation
    review: HumanReview | None
    executable: bool


class PolicyEnforcementService:
    def __init__(
        self,
        *,
        guardrails: GuardrailService | None = None,
    ) -> None:
        self.guardrails = guardrails or GuardrailService()

    async def enforce(
        self,
        *,
        session: AsyncSession,
        boundary: str,
        action: str,
        arguments: dict[str, Any],
        user_id: uuid.UUID,
        conversation_id: uuid.UUID | None = None,
        message_id: uuid.UUID | None = None,
        workflow_id: str | None = None,
        resource: str | None = None,
        request_content: str | None = None,
        approval_granted: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> PolicyEnforcementResult:
        started_at = time.perf_counter()

        evaluation = await self.guardrails.evaluate(
            GuardrailRequest(
                action=GuardrailAction(
                    action=action,
                    resource=resource,
                    arguments=arguments,
                ),
                agent_id=(metadata or {}).get("agent_id"),
                user_id=str(user_id),
                workflow_id=workflow_id,
                metadata=metadata or {},
            )
        )

        POLICY_EVALUATION_DURATION_SECONDS.labels(
            source=evaluation.source,
        ).observe(max(time.perf_counter() - started_at, 0.0))

        POLICY_EVALUATIONS_TOTAL.labels(
            decision=evaluation.decision.value,
            risk=evaluation.risk.value,
            source=evaluation.source,
        ).inc()

        review: HumanReview | None = None

        if evaluation.decision == GuardrailDecision.REVIEW:
            if approval_granted:
                executable = True
                outcome = "approved_review"
            elif conversation_id is not None:
                review = await HumanReviewService.create(
                    session=session,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    message_id=message_id,
                    reason=(
                        f"Policy {evaluation.policy_version}: "
                        f"{evaluation.reason}"
                    ),
                    requested_action=action,
                    request_content=request_content,
                    action_payload={
                        "policy_guardrail": True,
                        "boundary": boundary,
                        "action": action,
                        "resource": resource,
                        "arguments": arguments,
                        "workflow_id": workflow_id,
                        "matched_rules": list(
                            evaluation.matched_rules
                        ),
                        "policy_version": evaluation.policy_version,
                    },
                    commit=False,
                )
                executable = False
                outcome = "review_created"
                POLICY_REVIEW_CREATED_TOTAL.labels(
                    boundary=boundary,
                ).inc()
            else:
                executable = False
                outcome = "review_required"

        elif evaluation.decision == GuardrailDecision.DENY:
            executable = False
            outcome = "denied"

        else:
            executable = True
            outcome = "allowed"

        POLICY_ENFORCEMENT_TOTAL.labels(
            boundary=boundary,
            outcome=outcome,
        ).inc()

        await PolicyAuditService.record(
            session=session,
            boundary=boundary,
            action=action,
            evaluation=evaluation,
            user_id=user_id,
            conversation_id=conversation_id,
            review_id=(review.id if review else None),
            resource=resource,
            metadata={
                **(metadata or {}),
                "approval_granted": approval_granted,
                "enforcement_outcome": outcome,
            },
            commit=False,
        )

        await session.commit()

        if review is not None:
            await session.refresh(review)

        return PolicyEnforcementResult(
            evaluation=evaluation,
            review=review,
            executable=executable,
        )


policy_enforcement_service = PolicyEnforcementService()
