from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.adaptive_governance_v13.schemas import (
    GovernanceSignalCreate,
    GovernanceSignalResponse,
    GovernanceSummaryResponse,
    PolicyProposalCreate,
    PolicyProposalResponse,
    PolicyRecommendationRequest,
    PolicyRecommendationResponse,
    ProposalApplyRequest,
    ProposalReviewRequest,
    ProposalRollbackRequest,
    ShadowEvaluationRequest,
    ShadowEvaluationResponse,
)
from app.adaptive_governance_v13.service import (
    AdaptiveGovernanceService,
    InvalidProposalTransitionError,
    ProposalNotFoundError,
)
from app.api.dependencies import CurrentUser, DatabaseSession


router = APIRouter(
    prefix="/adaptive-governance/v13",
    tags=["V13 Adaptive Governance"],
)
service = AdaptiveGovernanceService()


@router.post("/signals", response_model=GovernanceSignalResponse, status_code=status.HTTP_201_CREATED)
async def ingest_signal(
    payload: GovernanceSignalCreate,
    current_user: CurrentUser,
    session: DatabaseSession,
):
    row = await service.ingest_signal(session=session, user_id=current_user.id, payload=payload)
    return GovernanceSignalResponse.model_validate(row)


@router.post("/recommendations", response_model=PolicyRecommendationResponse)
async def recommendation(
    payload: PolicyRecommendationRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
):
    return await service.recommend(session=session, user_id=current_user.id, payload=payload)


@router.post("/proposals", response_model=PolicyProposalResponse, status_code=status.HTTP_201_CREATED)
async def create_proposal(
    payload: PolicyProposalCreate,
    current_user: CurrentUser,
    session: DatabaseSession,
):
    row = await service.create_proposal(session=session, user_id=current_user.id, payload=payload)
    return PolicyProposalResponse.model_validate(row)


@router.post("/proposals/{proposal_id}/review", response_model=PolicyProposalResponse)
async def review(
    proposal_id: UUID,
    payload: ProposalReviewRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
):
    try:
        row = await service.review(
            session=session,
            user_id=current_user.id,
            reviewer_id=current_user.id,
            proposal_id=proposal_id,
            payload=payload,
        )
    except ProposalNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidProposalTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return PolicyProposalResponse.model_validate(row)


@router.post("/proposals/{proposal_id}/shadow-evaluate", response_model=ShadowEvaluationResponse)
async def shadow_evaluate(
    proposal_id: UUID,
    payload: ShadowEvaluationRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
):
    try:
        return await service.shadow_evaluate(
            session=session,
            user_id=current_user.id,
            proposal_id=proposal_id,
            payload=payload,
        )
    except ProposalNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/proposals/{proposal_id}/apply", response_model=PolicyProposalResponse)
async def apply(
    proposal_id: UUID,
    payload: ProposalApplyRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
):
    try:
        row = await service.apply(
            session=session,
            user_id=current_user.id,
            proposal_id=proposal_id,
            payload=payload,
        )
    except ProposalNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidProposalTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return PolicyProposalResponse.model_validate(row)


@router.post("/proposals/{proposal_id}/rollback", response_model=PolicyProposalResponse)
async def rollback(
    proposal_id: UUID,
    payload: ProposalRollbackRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
):
    try:
        row = await service.rollback(
            session=session,
            user_id=current_user.id,
            proposal_id=proposal_id,
            payload=payload,
        )
    except ProposalNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidProposalTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return PolicyProposalResponse.model_validate(row)


@router.get("/summary", response_model=GovernanceSummaryResponse)
async def summary(
    current_user: CurrentUser,
    session: DatabaseSession,
):
    return await service.summary(session=session, user_id=current_user.id)
