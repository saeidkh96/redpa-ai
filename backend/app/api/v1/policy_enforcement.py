from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.schemas.policy_enforcement import (
    PolicyAuditEventResponse,
    PolicyEnforcementRequest,
    PolicyEnforcementResponse,
)
from app.services.policy_audit_service import PolicyAuditService
from app.schemas.policy_overrides_v10 import (
    PolicyOverrideCreate,
    PolicyOverrideResponse,
    PolicyOverrideUpdate,
)
from app.services.policy_override_v10_service import (
    PolicyOverrideConflictError,
    PolicyOverrideNotFoundError,
    policy_override_v10_service,
)
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


@router.get("/overrides", response_model=list[PolicyOverrideResponse])
async def list_policy_overrides(
    current_user: CurrentUser,
    session: DatabaseSession,
) -> list[PolicyOverrideResponse]:
    items = await policy_override_v10_service.list(session=session, user_id=current_user.id)
    return [PolicyOverrideResponse.model_validate(item) for item in items]


@router.post("/overrides", response_model=PolicyOverrideResponse, status_code=status.HTTP_201_CREATED)
async def create_policy_override(
    payload: PolicyOverrideCreate,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> PolicyOverrideResponse:
    try:
        item = await policy_override_v10_service.create(
            session=session, user_id=current_user.id, payload=payload
        )
    except PolicyOverrideConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return PolicyOverrideResponse.model_validate(item)


@router.patch("/overrides/{override_id}", response_model=PolicyOverrideResponse)
async def update_policy_override(
    override_id: uuid.UUID,
    payload: PolicyOverrideUpdate,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> PolicyOverrideResponse:
    try:
        item = await policy_override_v10_service.update(
            session=session,
            user_id=current_user.id,
            override_id=override_id,
            payload=payload,
        )
    except PolicyOverrideNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return PolicyOverrideResponse.model_validate(item)


@router.delete("/overrides/{override_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy_override(
    override_id: uuid.UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> Response:
    try:
        await policy_override_v10_service.delete(
            session=session, user_id=current_user.id, override_id=override_id
        )
    except PolicyOverrideNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
