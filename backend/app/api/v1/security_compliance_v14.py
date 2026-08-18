from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from app.api.dependencies import CurrentUser, DatabaseSession
from app.security_compliance_v14.exporter import compliance_record_exporter
from app.security_compliance_v14.repository import SecurityComplianceRepository
from app.security_compliance_v14.schemas import (
    ComplianceControlCreate, ComplianceControlResponse, ComplianceEvidenceCreate,
    ComplianceEvidenceResponse, ComplianceRecordResponse, EvidenceApprovalRequest,
    EvidenceAssessmentRequest, EvidenceAssessmentResponse,
)
from app.security_compliance_v14.service import (
    ComplianceRecordNotFoundError, ControlNotFoundError,
    InvalidComplianceTransitionError, SecurityComplianceService,
)

router = APIRouter(prefix="/security-compliance/v14", tags=["V14 Security & Compliance Evidence"])
service = SecurityComplianceService()

@router.post("/controls", response_model=ComplianceControlResponse, status_code=status.HTTP_201_CREATED)
async def create_control(payload: ComplianceControlCreate, current_user: CurrentUser, session: DatabaseSession):
    return ComplianceControlResponse.model_validate(await service.create_control(session=session,user_id=current_user.id,payload=payload))

@router.post("/evidence", response_model=ComplianceEvidenceResponse, status_code=status.HTTP_201_CREATED)
async def collect_evidence(payload: ComplianceEvidenceCreate, current_user: CurrentUser, session: DatabaseSession):
    try:
        row = await service.collect_evidence(session=session,user_id=current_user.id,payload=payload)
    except ControlNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ComplianceEvidenceResponse.model_validate(row)

@router.post("/evidence/{evidence_id}/verify", response_model=ComplianceEvidenceResponse)
async def verify_evidence(evidence_id: UUID, current_user: CurrentUser, session: DatabaseSession):
    try:
        row = await service.verify_evidence(session=session,user_id=current_user.id,evidence_id=evidence_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ComplianceEvidenceResponse.model_validate(row)

@router.post("/assessments", response_model=EvidenceAssessmentResponse)
async def assess(payload: EvidenceAssessmentRequest, current_user: CurrentUser, session: DatabaseSession):
    try:
        assessment, _ = await service.assess(session=session,user_id=current_user.id,payload=payload)
    except ControlNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return assessment

@router.post("/records/{record_id}/review", response_model=ComplianceRecordResponse)
async def review_record(record_id: UUID, payload: EvidenceApprovalRequest, current_user: CurrentUser, session: DatabaseSession):
    try:
        row = await service.approve_record(session=session,user_id=current_user.id,reviewer_id=current_user.id,record_id=record_id,payload=payload)
    except ComplianceRecordNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidComplianceTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return ComplianceRecordResponse.model_validate(row)

@router.get("/records/{record_id}/export")
async def export_record(record_id: UUID, current_user: CurrentUser, session: DatabaseSession):
    row = await SecurityComplianceRepository.get_record(session=session,user_id=current_user.id,record_id=record_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Compliance record not found.")
    return compliance_record_exporter.export(row)
