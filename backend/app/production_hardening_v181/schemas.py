from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

StageStatus = Literal["pass", "fail", "skipped"]

class HardeningStageResult(BaseModel):
    stage: int = Field(ge=1, le=10)
    name: str
    status: StageStatus
    detail: str
    evidence: dict[str, Any] = Field(default_factory=dict)

class ReleaseHardeningReport(BaseModel):
    version: str = "18.1.0"
    release_candidate: str
    overall_status: Literal["PASS", "FAIL"]
    stages: list[HardeningStageResult]
    generated_at: datetime

class HardeningRunCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    release_candidate: str = Field(default="v18.1.0-rc1", min_length=1, max_length=120)
    metadata: dict[str, Any] = Field(default_factory=dict)

class HardeningRunResponse(BaseModel):
    id: UUID
    release_candidate: str
    status: str
    report: dict[str, Any]
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
