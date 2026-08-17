from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.platform_evolution.schemas import (
    AdaptivePolicyRequest,
    AgentFailoverRequest,
    AgentRegistrationRequest,
    CloudReadinessRequest,
    ComplianceEvidenceRequest,
    ConnectorAssessmentRequest,
    EvolutionListResponse,
    EvolutionRecordResponse,
    ReliabilitySignalRequest,
    RolloutDecisionRequest,
)
from app.platform_evolution.service import platform_evolution_service


router = APIRouter(prefix="/platform/evolution", tags=["V11-V18 Platform Evolution"])


@router.get("/records", response_model=EvolutionListResponse)
async def list_records(
    current_user: CurrentUser,
    session: DatabaseSession,
    version: int | None = Query(default=None, ge=11, le=18),
) -> EvolutionListResponse:
    items, total = await platform_evolution_service.list_records(
        session=session, user_id=current_user.id, version=version
    )
    return EvolutionListResponse(
        items=[EvolutionRecordResponse.model_validate(item) for item in items],
        total=total,
    )


@router.post("/v11/reliability/evaluate", response_model=EvolutionRecordResponse, status_code=status.HTTP_201_CREATED)
async def v11_reliability(payload: ReliabilitySignalRequest, current_user: CurrentUser, session: DatabaseSession):
    return await platform_evolution_service.reliability(session=session, user_id=current_user.id, payload=payload)


@router.post("/v12/agents/failover", response_model=EvolutionRecordResponse, status_code=status.HTTP_201_CREATED)
async def v12_failover(payload: AgentFailoverRequest, current_user: CurrentUser, session: DatabaseSession):
    return await platform_evolution_service.failover(session=session, user_id=current_user.id, payload=payload)


@router.post("/v13/policy/recommend", response_model=EvolutionRecordResponse, status_code=status.HTTP_201_CREATED)
async def v13_policy(payload: AdaptivePolicyRequest, current_user: CurrentUser, session: DatabaseSession):
    return await platform_evolution_service.adaptive_policy(session=session, user_id=current_user.id, payload=payload)


@router.post("/v14/compliance/evidence", response_model=EvolutionRecordResponse, status_code=status.HTTP_201_CREATED)
async def v14_compliance(payload: ComplianceEvidenceRequest, current_user: CurrentUser, session: DatabaseSession):
    return await platform_evolution_service.compliance(session=session, user_id=current_user.id, payload=payload)


@router.post("/v15/cloud/readiness", response_model=EvolutionRecordResponse, status_code=status.HTTP_201_CREATED)
async def v15_cloud(payload: CloudReadinessRequest, current_user: CurrentUser, session: DatabaseSession):
    return await platform_evolution_service.cloud_readiness(session=session, user_id=current_user.id, payload=payload)


@router.post("/v16/rollouts/decide", response_model=EvolutionRecordResponse, status_code=status.HTTP_201_CREATED)
async def v16_rollout(payload: RolloutDecisionRequest, current_user: CurrentUser, session: DatabaseSession):
    return await platform_evolution_service.rollout(session=session, user_id=current_user.id, payload=payload)


@router.post("/v17/connectors/assess", response_model=EvolutionRecordResponse, status_code=status.HTTP_201_CREATED)
async def v17_connector(payload: ConnectorAssessmentRequest, current_user: CurrentUser, session: DatabaseSession):
    return await platform_evolution_service.connector(session=session, user_id=current_user.id, payload=payload)


@router.post("/v18/agents/register", response_model=EvolutionRecordResponse, status_code=status.HTTP_201_CREATED)
async def v18_registry(payload: AgentRegistrationRequest, current_user: CurrentUser, session: DatabaseSession):
    return await platform_evolution_service.register_agent(session=session, user_id=current_user.id, payload=payload)
