from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

IncidentSeverity = Literal['info','warning','critical']
IncidentStatus = Literal['open','diagnosed','mitigating','resolved','failed']
ActionStatus = Literal['planned','approved','executing','completed','failed','denied']


class IncidentCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    service: str = Field(min_length=2, max_length=120)
    summary: str = Field(min_length=3, max_length=500)
    severity: IncidentSeverity = 'warning'
    source: str = Field(default='manual', max_length=80)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IncidentRecord(BaseModel):
    id: UUID
    service: str
    summary: str
    severity: IncidentSeverity
    status: IncidentStatus
    source: str
    diagnosis: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None


class RemediationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    action: Literal['restart_container'] = 'restart_container'
    reason: str = Field(min_length=8, max_length=500)
    approved: bool = False


class OpsActionRecord(BaseModel):
    id: UUID
    incident_id: UUID
    action: str
    target: str
    status: ActionStatus
    approved: bool
    reason: str
    result: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class ContainerDiagnosis(BaseModel):
    container: str
    found: bool
    state: str | None = None
    health: str | None = None
    restart_count: int = 0
    recent_logs: list[str] = Field(default_factory=list)
    recommendation: str
    restart_allowed: bool


class CostEstimateRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    backend_replicas: int = Field(default=1, ge=0, le=100)
    worker_replicas: int = Field(default=1, ge=0, le=100)
    monthly_backend_replica_eur: float = Field(default=55.0, ge=0)
    monthly_worker_replica_eur: float = Field(default=40.0, ge=0)
    managed_data_services_eur: float = Field(default=180.0, ge=0)
    observability_eur: float = Field(default=45.0, ge=0)
    other_eur: float = Field(default=25.0, ge=0)


class CostEstimate(BaseModel):
    backend_eur: float
    workers_eur: float
    data_services_eur: float
    observability_eur: float
    other_eur: float
    monthly_total_eur: float
    annual_total_eur: float


class ReleaseReadinessRequest(BaseModel):
    availability: float = Field(ge=0, le=1)
    p95_latency_ms: float = Field(ge=0)
    availability_target: float = Field(default=0.99, ge=0, le=1)
    p95_latency_target_ms: float = Field(default=1000, gt=0)
    open_critical_incidents: int = Field(default=0, ge=0)
    security_gate_passed: bool = True
    regression_gate_passed: bool = True


class ReleaseReadinessDecision(BaseModel):
    decision: Literal['PROMOTE','HOLD']
    checks: dict[str, bool]
    reasons: list[str]
