from __future__ import annotations

from fastapi import APIRouter

from app.api.dependencies import CurrentUser
from app.guardrails.contracts import (
    GuardrailAction,
    GuardrailRequest,
)
from app.guardrails.service import guardrail_service
from app.schemas.guardrails import (
    GuardrailEvaluationRequest,
    GuardrailEvaluationResponse,
    GuardrailHealthResponse,
)


router = APIRouter(
    prefix="/guardrails",
    tags=["Guardrails"],
)


@router.post(
    "/evaluate",
    response_model=GuardrailEvaluationResponse,
)
async def evaluate_policy(
    request: GuardrailEvaluationRequest,
    current_user: CurrentUser,
) -> GuardrailEvaluationResponse:
    evaluation = await guardrail_service.evaluate(
        GuardrailRequest(
            action=GuardrailAction(
                action=request.action,
                resource=request.resource,
                arguments=request.arguments,
            ),
            agent_id=request.agent_id,
            user_id=str(current_user.id),
            workflow_id=request.workflow_id,
            metadata=request.metadata,
        )
    )

    return GuardrailEvaluationResponse(
        decision=evaluation.decision,
        risk=evaluation.risk,
        reason=evaluation.reason,
        matched_rules=list(evaluation.matched_rules),
        policy_version=evaluation.policy_version,
        source=evaluation.source,
    )


@router.get(
    "/health",
    response_model=GuardrailHealthResponse,
)
async def guardrail_health(
    current_user: CurrentUser,
) -> GuardrailHealthResponse:
    del current_user

    healthy = await guardrail_service.healthy()

    return GuardrailHealthResponse(
        policy_service="healthy" if healthy else "unavailable",
    )
