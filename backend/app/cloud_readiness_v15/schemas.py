from __future__ import annotations
from pydantic import BaseModel, Field

class CloudReadinessInput(BaseModel):
    environment: str = Field(min_length=1, max_length=120)
    health_checks: bool = True
    dependency_checks: bool = True
    backups: bool = False
    restore_tested: bool = False
    secrets_manager: bool = False
    least_privilege_iam: bool = False
    autoscaling: bool = False
    capacity_tested: bool = False
    telemetry: bool = True
    alerting: bool = False
    disaster_recovery: bool = False
    multi_zone: bool = False

class CloudReadinessResult(BaseModel):
    environment: str
    score: float
    status: str
    missing_controls: list[str]
    deployment_allowed: bool
