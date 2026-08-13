import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    status,
)

from app.api.dependencies import (
    CurrentUser,
    DatabaseSession,
)
from app.models.human_review import HumanReviewStatus
from app.schemas.human_review import (
    HumanReviewDecisionRequest,
    HumanReviewListResponse,
    HumanReviewResponse,
)
from app.services.human_review_service import (
    HumanReviewAlreadyDecidedError,
    HumanReviewNotFoundError,
    HumanReviewService,
)
from app.services.workflow_resume_service import (
    WorkflowAlreadyResumedError,
    WorkflowResumeConversationNotFoundError,
    WorkflowResumeNotApprovedError,
    WorkflowResumeReviewNotFoundError,
    WorkflowResumeService,
)


router = APIRouter(
    prefix="/reviews",
    tags=["Human Reviews"],
)


@router.get(
    "",
    response_model=HumanReviewListResponse,
    status_code=status.HTTP_200_OK,
    summary="List current user's human reviews",
)
async def list_human_reviews(
    current_user: CurrentUser,
    session: DatabaseSession,
    review_status: Annotated[
        HumanReviewStatus | None,
        Query(
            alias="status",
            description=(
                "Optionally filter reviews by their current status."
            ),
        ),
    ] = None,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
            description="Maximum number of reviews to return.",
        ),
    ] = 20,
    offset: Annotated[
        int,
        Query(
            ge=0,
            description="Number of reviews to skip.",
        ),
    ] = 0,
) -> HumanReviewListResponse:
    reviews, total = await HumanReviewService.get_all_for_user(
        session=session,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        review_status=review_status,
    )

    return HumanReviewListResponse(
        items=[
            HumanReviewResponse.model_validate(
                review,
            )
            for review in reviews
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{review_id}",
    response_model=HumanReviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a human review",
)
async def get_human_review(
    review_id: uuid.UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> HumanReviewResponse:
    review = await HumanReviewService.get_by_id(
        session=session,
        review_id=review_id,
        user_id=current_user.id,
    )

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Human review not found.",
        )

    return HumanReviewResponse.model_validate(
        review,
    )


@router.post(
    "/{review_id}/approve",
    response_model=HumanReviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve a pending human review",
)
async def approve_human_review(
    review_id: uuid.UUID,
    decision_data: HumanReviewDecisionRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> HumanReviewResponse:
    try:
        review = await HumanReviewService.approve(
            session=session,
            review_id=review_id,
            user_id=current_user.id,
            reviewer_id=current_user.id,
            feedback=decision_data.feedback,
        )

    except HumanReviewNotFoundError as exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                exception,
            ),
        ) from exception

    except HumanReviewAlreadyDecidedError as exception:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(
                exception,
            ),
        ) from exception

    return HumanReviewResponse.model_validate(
        review,
    )


@router.post(
    "/{review_id}/reject",
    response_model=HumanReviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject a pending human review",
)
async def reject_human_review(
    review_id: uuid.UUID,
    decision_data: HumanReviewDecisionRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> HumanReviewResponse:
    try:
        review = await HumanReviewService.reject(
            session=session,
            review_id=review_id,
            user_id=current_user.id,
            reviewer_id=current_user.id,
            feedback=decision_data.feedback,
        )

    except HumanReviewNotFoundError as exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                exception,
            ),
        ) from exception

    except HumanReviewAlreadyDecidedError as exception:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(
                exception,
            ),
        ) from exception

    return HumanReviewResponse.model_validate(
        review,
    )


@router.post(
    "/{review_id}/resume",
    response_model=HumanReviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Resume an approved human-review workflow",
    description=(
        "Resume the workflow associated with an approved human "
        "review. The approved action is executed through the "
        "LangGraph workflow and the resulting assistant message "
        "is stored in the conversation."
    ),
)
async def resume_human_review_workflow(
    review_id: uuid.UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> HumanReviewResponse:
    try:
        resume_result = (
            await WorkflowResumeService.resume_approved_review(
                session=session,
                review_id=review_id,
                user_id=current_user.id,
            )
        )

    except WorkflowResumeReviewNotFoundError as exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                exception,
            ),
        ) from exception

    except WorkflowResumeConversationNotFoundError as exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                exception,
            ),
        ) from exception

    except WorkflowResumeNotApprovedError as exception:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(
                exception,
            ),
        ) from exception

    except WorkflowAlreadyResumedError as exception:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(
                exception,
            ),
        ) from exception

    return HumanReviewResponse.model_validate(
        resume_result.review,
    )