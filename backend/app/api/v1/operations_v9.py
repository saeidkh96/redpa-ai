from __future__ import annotations
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.api.dependencies import CurrentUser, DatabaseSession
from app.governance_v10.schemas import AgentRunResponse
from app.ops_v9.governance import OpsGovernanceBridge

from app.ops_v9.cost import CostEstimator
from app.ops_v9.readiness import ReleaseReadinessEvaluator
from app.ops_v9.repository import IncidentNotFoundError, OpsRepository
from app.ops_v9.schemas import (
    CostEstimate, CostEstimateRequest, IncidentCreate, IncidentRecord,
    OpsActionRecord, ReleaseReadinessDecision, ReleaseReadinessRequest,
    RemediationRequest,
)
from app.ops_v9.service import OpsService

router = APIRouter(prefix='/operations/v9', tags=['V9 Production Operations'])


@router.post('/incidents', response_model=IncidentRecord, status_code=201)
async def create_incident(payload: IncidentCreate) -> IncidentRecord:
    return await OpsRepository.create_incident(payload)


@router.post('/incidents/{incident_id}/governance-run', response_model=AgentRunResponse, status_code=201)
async def start_incident_governance_run(
    incident_id: UUID, current_user: CurrentUser, session: DatabaseSession,
) -> AgentRunResponse:
    try:
        incident = await OpsRepository.get_incident(incident_id)
    except IncidentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return await OpsGovernanceBridge.start_incident_run(
        session=session, user_id=current_user.id, incident=incident
    )


@router.get('/incidents', response_model=list[IncidentRecord])
async def list_incidents(limit: int = Query(default=100, ge=1, le=500)) -> list[IncidentRecord]:
    return await OpsRepository.list_incidents(limit)


@router.post('/incidents/{incident_id}/diagnose', response_model=IncidentRecord)
async def diagnose_incident(incident_id: UUID) -> IncidentRecord:
    try:
        return await OpsService.diagnose(incident_id)
    except IncidentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post('/incidents/{incident_id}/remediate', response_model=OpsActionRecord)
async def remediate_incident(incident_id: UUID, payload: RemediationRequest) -> OpsActionRecord:
    try:
        return await OpsService.remediate(incident_id, payload)
    except IncidentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post('/cost/estimate', response_model=CostEstimate)
async def estimate_cost(payload: CostEstimateRequest) -> CostEstimate:
    return CostEstimator.estimate(payload)


@router.post('/release/readiness', response_model=ReleaseReadinessDecision)
async def release_readiness(payload: ReleaseReadinessRequest) -> ReleaseReadinessDecision:
    return ReleaseReadinessEvaluator.evaluate(payload)


@router.post('/incidents/{incident_id}/governed/{run_id}/diagnose', response_model=IncidentRecord)
async def diagnose_incident_governed(
    incident_id: UUID, run_id: UUID, current_user: CurrentUser, session: DatabaseSession,
) -> IncidentRecord:
    try:
        return await OpsService.diagnose_governed(
            incident_id, session=session, user_id=current_user.id, run_id=run_id
        )
    except IncidentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post('/incidents/{incident_id}/governed/{run_id}/remediate', response_model=OpsActionRecord)
async def remediate_incident_governed(
    incident_id: UUID, run_id: UUID, payload: RemediationRequest,
    current_user: CurrentUser, session: DatabaseSession,
) -> OpsActionRecord:
    try:
        return await OpsService.remediate_governed(
            incident_id, payload, session=session, user_id=current_user.id, run_id=run_id
        )
    except IncidentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
