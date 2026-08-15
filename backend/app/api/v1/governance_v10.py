from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.governance_v10.repository import AgentRunNotFoundError, AgentRunRepository
from app.governance_v10.schemas import (
    AgentRunCreate,
    AgentRunEventCreate,
    AgentRunEventResponse,
    AgentRunListResponse,
    AgentRunResponse,
    AgentRunUpdate,
    RunEvaluationRequest,
    RunEvaluationResponse,
    RunPolicyCheckRequest,
    RunPolicyCheckResponse,
)
from app.governance_v10.service import AgentGovernanceService, InvalidAgentRunTransitionError
from app.models.governance_v10 import AgentRunStatus


router = APIRouter(prefix="/governance/v10", tags=["V10 Agent Governance"])
service = AgentGovernanceService()


@router.post("/runs", response_model=AgentRunResponse, status_code=status.HTTP_201_CREATED)
async def create_run(payload: AgentRunCreate, current_user: CurrentUser, session: DatabaseSession) -> AgentRunResponse:
    run = await service.create_run(session=session, user_id=current_user.id, payload=payload)
    return AgentRunResponse.model_validate(run)


@router.get("/runs", response_model=AgentRunListResponse)
async def list_runs(
    current_user: CurrentUser,
    session: DatabaseSession,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    agent_id: str | None = Query(default=None, max_length=150),
    run_status: AgentRunStatus | None = Query(default=None, alias="status"),
) -> AgentRunListResponse:
    items, total = await AgentRunRepository.list(
        session=session,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        agent_id=agent_id,
        status=run_status.value if run_status else None,
    )
    return AgentRunListResponse(
        items=[AgentRunResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/runs/{run_id}", response_model=AgentRunResponse)
async def get_run(run_id: uuid.UUID, current_user: CurrentUser, session: DatabaseSession) -> AgentRunResponse:
    try:
        run = await AgentRunRepository.get(session=session, run_id=run_id, user_id=current_user.id)
    except AgentRunNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return AgentRunResponse.model_validate(run)


@router.patch("/runs/{run_id}", response_model=AgentRunResponse)
async def update_run(run_id: uuid.UUID, payload: AgentRunUpdate, current_user: CurrentUser, session: DatabaseSession) -> AgentRunResponse:
    try:
        run = await service.update_run(session=session, run_id=run_id, user_id=current_user.id, payload=payload)
    except AgentRunNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidAgentRunTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return AgentRunResponse.model_validate(run)


@router.post("/runs/{run_id}/events", response_model=AgentRunEventResponse, status_code=status.HTTP_201_CREATED)
async def add_run_event(run_id: uuid.UUID, payload: AgentRunEventCreate, current_user: CurrentUser, session: DatabaseSession) -> AgentRunEventResponse:
    try:
        event = await service.add_event(session=session, run_id=run_id, user_id=current_user.id, payload=payload)
    except AgentRunNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return AgentRunEventResponse.model_validate(event)


@router.post("/runs/{run_id}/policy-check", response_model=RunPolicyCheckResponse)
async def policy_check(run_id: uuid.UUID, payload: RunPolicyCheckRequest, current_user: CurrentUser, session: DatabaseSession) -> RunPolicyCheckResponse:
    try:
        return await service.policy_check(session=session, run_id=run_id, user_id=current_user.id, payload=payload)
    except AgentRunNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/runs/{run_id}/evaluate", response_model=RunEvaluationResponse)
async def evaluate_run(run_id: uuid.UUID, payload: RunEvaluationRequest, current_user: CurrentUser, session: DatabaseSession) -> RunEvaluationResponse:
    try:
        return await service.evaluate_run(session=session, run_id=run_id, user_id=current_user.id, payload=payload)
    except AgentRunNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
