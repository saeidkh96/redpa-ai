from __future__ import annotations
from datetime import datetime
from typing import Any, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

ControlSeverity = Literal["low", "medium", "high", "critical"]
EvidenceStatus = Literal["complete", "incomplete", "invalid", "expired", "verified"]
AssessmentStatus = Literal["pass", "review", "fail"]

class ComplianceControlCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    control_id: str = Field(min_length=1, max_length=120)
    framework: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=250)
    description: str = Field(min_length=1, max_length=2000)
    severity: ControlSeverity = "medium"
    required_fields: list[str] = Field(default_factory=list)
    required_evidence_types: list[str] = Field(default_factory=list)
    approval_required: bool = False

class ComplianceControlResponse(ComplianceControlCreate):
    id: UUID
    version: int
    active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ComplianceEvidenceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    control_id: str = Field(min_length=1, max_length=120)
    evidence_type: str = Field(min_length=1, max_length=120)
    source: str = Field(min_length=1, max_length=250)
    subject: str = Field(min_length=1, max_length=250)
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    collected_at: datetime | None = None
    expires_at: datetime | None = None
    content_hash: str | None = Field(default=None, max_length=128)

class ComplianceEvidenceResponse(BaseModel):
    id: UUID
    user_id: UUID
    control_id: str
    evidence_type: str
    source: str
    subject: str
    payload: dict[str, Any]
    metadata: dict[str, Any]
    status: EvidenceStatus
    content_hash: str
    collected_at: datetime
    expires_at: datetime | None
    verified_at: datetime | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class EvidenceAssessmentRequest(BaseModel):
    control_id: str = Field(min_length=1, max_length=120)
    evidence_ids: list[UUID] = Field(min_length=1)
    strict_integrity: bool = True

class EvidenceFinding(BaseModel):
    code: str
    message: str
    severity: ControlSeverity

class EvidenceAssessmentResponse(BaseModel):
    control_id: str
    status: AssessmentStatus
    completeness_score: float = Field(ge=0.0, le=1.0)
    integrity_score: float = Field(ge=0.0, le=1.0)
    freshness_score: float = Field(ge=0.0, le=1.0)
    risk_score: float = Field(ge=0.0, le=1.0)
    missing_fields: list[str]
    missing_evidence_types: list[str]
    findings: list[EvidenceFinding]
    approval_required: bool

class EvidenceApprovalRequest(BaseModel):
    approved: bool
    reason: str = Field(min_length=4, max_length=1000)

class ComplianceRecordResponse(BaseModel):
    id: UUID
    control_id: str
    assessment_status: AssessmentStatus
    approval_status: str
    assessment: dict[str, Any]
    evidence_snapshot: list[dict[str, Any]]
    approved_by: UUID | None
    approved_at: datetime | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ComplianceSummaryResponse(BaseModel):
    controls: int
    evidence_items: int
    records: int
    pass_count: int
    review_count: int
    fail_count: int
