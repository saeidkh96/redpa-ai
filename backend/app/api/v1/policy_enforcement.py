from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.dependencies import CurrentUser, DatabaseSession
from app.schemas.policy_enforcement import (
    PolicyAuditEventResponse,
    PolicyEnforcementRequest,
    PolicyEnforcementResponse,
)
from app.services.policy_audit_service import PolicyAuditService
from app.services.policy_enforcement_service import (
    policy_enforcement_service,
)


router = APIRouter(
    prefix="/policy",
    tags=["Policy Enforcement"],
)


@router.post(
    "/enforce",
    response_model=PolicyEnforcementResponse,
)
async def enforce_policy(
    request: PolicyEnforcementRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> PolicyEnforcementResponse:
    result = await policy_enforcement_service.enforce(
        session=session,
        boundary=request.boundary,
        action=request.action,
        arguments=request.arguments,
        user_id=current_user.id,
        conversation_id=request.conversation_id,
        message_id=request.message_id,
        workflow_id=request.workflow_id,
        resource=request.resource,
        request_content=request.request_content,
        approval_granted=request.approval_granted,
        metadata=request.metadata,
    )

    return PolicyEnforcementResponse(
        decision=result.evaluation.decision,
        risk=result.evaluation.risk,
        reason=result.evaluation.reason,
        matched_rules=list(result.evaluation.matched_rules),
        policy_version=result.evaluation.policy_version,
        source=result.evaluation.source,
        executable=result.executable,
        review_id=(result.review.id if result.review else None),
    )


@router.get(
    "/audit",
    response_model=list[PolicyAuditEventResponse],
)
async def list_policy_audit_events(
    current_user: CurrentUser,
    session: DatabaseSession,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[PolicyAuditEventResponse]:
    events = await PolicyAuditService.list_for_user(
        session=session,
        user_id=current_user.id,
        limit=limit,
    )
    return [
        PolicyAuditEventResponse.model_validate(event)
        for event in events
    ]
