from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class ProductionDemoRequest(BaseModel):
    task: str = Field(
        default="List the running Docker containers and return a concise runtime summary.",
        min_length=1,
        max_length=1000,
    )
    primary_agent: str = Field(default="research-agent", min_length=1, max_length=100)
    fallback_agent: str = Field(default="docker-agent", min_length=1, max_length=100)
    inject_primary_failure: bool = True
    approval_granted: bool = False


class DemoStage(BaseModel):
    stage: int
    name: str
    status: Literal["PASS", "FAIL", "BLOCKED"]
    detail: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class ProductionDemoResult(BaseModel):
    demo_id: str
    status: Literal["PASS", "FAIL", "BLOCKED"]
    task: str
    primary_agent: str
    fallback_agent: str
    stages: list[DemoStage]
    final_response: dict[str, Any] | None = None
    evidence_path: str | None = None
