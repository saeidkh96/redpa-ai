from __future__ import annotations

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.agents.state import AgentRoute


class PlannerResult(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    route: AgentRoute

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    reasoning: str = Field(
        min_length=1,
        max_length=1000,
    )

    signals: list[str] = Field(
        default_factory=list,
        max_length=10,
    )

    @field_validator("signals")
    @classmethod
    def normalize_signals(
        cls,
        values: list[str],
    ) -> list[str]:
        normalized_signals: list[str] = []

        for value in values:
            normalized_value = str(value).strip()

            if not normalized_value:
                continue

            if normalized_value in normalized_signals:
                continue

            normalized_signals.append(
                normalized_value
            )

        return normalized_signals[:10]


class PlannerExecutionResult(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    plan: PlannerResult

    provider: str = Field(
        min_length=1,
    )

    model: str = Field(
        min_length=1,
    )

    fallback_used: bool = False

    error: str | None = None

    latency_ms: float = Field(
        default=0.0,
        ge=0.0,
    )