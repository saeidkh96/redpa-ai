from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


ResearchRunStatus = Literal[
    "queued",
    "running",
    "completed",
    "failed",
]


class EnterpriseResearchRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    query: str = Field(min_length=3, max_length=2000)
    max_results: int = Field(default=8, ge=3, le=20)
    minimum_quality_score: float = Field(default=0.65, ge=0.0, le=1.0)


class ResearchEvidenceItem(BaseModel):
    title: str
    url: str
    snippet: str
    source_domain: str
    score: float


class ResearchQuality(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    coverage_score: float = Field(ge=0.0, le=1.0)
    source_diversity_score: float = Field(ge=0.0, le=1.0)
    evidence_count: int = Field(ge=0)
    unique_domains: int = Field(ge=0)
    passed: bool


class ResearchTimelineEvent(BaseModel):
    id: UUID
    stage: str
    status: str
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class EnterpriseResearchRun(BaseModel):
    id: UUID
    query: str
    status: ResearchRunStatus
    current_stage: str
    progress: int = Field(ge=0, le=100)
    max_results: int
    minimum_quality_score: float
    provider: str | None = None
    report: str | None = None
    evidence: list[ResearchEvidenceItem] = Field(default_factory=list)
    quality: ResearchQuality | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None


class EnterpriseResearchRunDetail(EnterpriseResearchRun):
    timeline: list[ResearchTimelineEvent] = Field(default_factory=list)


class EnterpriseResearchRunList(BaseModel):
    items: list[EnterpriseResearchRun]
    total: int
