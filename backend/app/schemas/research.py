from __future__ import annotations

from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class ResearchEvidence(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    source_number: int = Field(
        ge=1,
    )

    title: str = Field(
        min_length=1,
        max_length=1000,
    )

    url: str = Field(
        min_length=1,
        max_length=4000,
    )

    snippet: str = Field(
        default="",
        max_length=6000,
    )

    provider: str = Field(
        default="web",
        min_length=1,
        max_length=100,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class ResearchResult(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    query: str = Field(
        min_length=1,
        max_length=1000,
    )

    answer: str = Field(
        min_length=1,
    )

    evidence: list[ResearchEvidence] = Field(
        default_factory=list,
    )

    provider: str = Field(
        min_length=1,
    )

    model: str = Field(
        min_length=1,
    )

    execution_time_ms: float = Field(
        ge=0.0,
    )

    usage: dict[str, Any] = Field(
        default_factory=dict,
    )
