from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OrchestratorResult(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    response_content: str = Field(
        min_length=1,
    )

    model: str = Field(
        min_length=1,
    )

    provider: str = Field(
        min_length=1,
    )

    route: str = Field(
        min_length=1,
    )

    planner_reason: str = Field(
        min_length=1,
    )

    usage: dict[str, Any] = Field(
        default_factory=dict,
    )