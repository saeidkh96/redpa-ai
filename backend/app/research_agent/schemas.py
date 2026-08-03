from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ResearchEvidence(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    title: str
    url: str
    snippet: str
    source_domain: str
    score: float = Field(
        ge=0.0,
    )


class ResearchResult(BaseModel):
    query: str
    summary: str
    evidence: list[ResearchEvidence]
    total_results: int
    provider: str
