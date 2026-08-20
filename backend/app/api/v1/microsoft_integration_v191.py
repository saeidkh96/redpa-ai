from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.services.human_review_service import (
    HumanReviewAlreadyDecidedError,
    HumanReviewNotFoundError,
)
from app.microsoft_integration_v191.schemas import (
    MicrosoftApprovalDecision,
    MicrosoftApprovalDecisionResult,
    MicrosoftApprovalEnvelope,
    MicrosoftApprovalRequest,
)
from app.microsoft_integration_v191.service import (
    microsoft_governed_approval_service,
)


router = APIRouter(
    prefix="/integrations/microsoft/v19.1",
    tags=["V19.1 Microsoft Governed Approval"],
)


@router.post(
    "/power-automate/approval",
    response_model=MicrosoftApprovalEnvelope,
    status_code=status.HTTP_201_CREATED,
)
async def create_power_automate_approval(
    payload: MicrosoftApprovalRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> MicrosoftApprovalEnvelope:
    return await microsoft_governed_approval_service.create_approval(
        session=session,
        user_id=current_user.id,
        payload=payload,
    )


@router.post(
    "/power-automate/approval/{review_id}/decision",
    response_model=MicrosoftApprovalDecisionResult,
    status_code=status.HTTP_200_OK,
)
async def apply_power_automate_decision(
    review_id: UUID,
    payload: MicrosoftApprovalDecision,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> MicrosoftApprovalDecisionResult:
    try:
        return await microsoft_governed_approval_service.apply_decision(
            session=session,
            user_id=current_user.id,
            review_id=review_id,
            payload=payload,
        )

    except HumanReviewNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except HumanReviewAlreadyDecidedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get("/capabilities")
async def capabilities(
    current_user: CurrentUser,
) -> dict:
    return {
        "version": "19.1",
        "power_automate": {
            "approval_request": True,
            "decision_callback": True,
            "persistent_human_review": True,
            "governance_event_recording": True,
        },
        "live_tenant_connection": False,
        "credentials_embedded": False,
    }
