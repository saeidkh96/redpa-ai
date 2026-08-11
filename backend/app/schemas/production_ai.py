from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.model_gateway.contracts import LLMCapability


class RuntimeToolCall(BaseModel):
    source: Literal["internal", "mcp"] = "internal"
    name: str = Field(min_length=1, max_length=200)
    arguments: dict[str, Any] = Field(default_factory=dict)
    approval_granted: bool = False


class ProductionRuntimeRequest(BaseModel):
    tenant_id: UUID
    agent_id: str = Field(min_length=1, max_length=150)
    prompt: str = Field(min_length=1)
    provider: str | None = Field(default=None, max_length=100)
    model: str | None = Field(default=None, max_length=200)
    capability: LLMCapability = LLMCapability.CHAT
    context: list[str] = Field(default_factory=list)
    business_rules: list[str] = Field(default_factory=list)
    tool_calls: list[RuntimeToolCall] = Field(default_factory=list)
    max_tokens: int | None = Field(default=512, gt=0)
    max_latency_ms: float | None = Field(default=None, gt=0)
    max_cost_usd: float | None = Field(default=None, gt=0)
    idempotency_key: str | None = Field(default=None, max_length=200)


class GuardrailStageResponse(BaseModel):
    decision: str
    reasons: list[str]


class RuntimeEvaluationResponse(BaseModel):
    outcome: str
    score: float
    reasons: list[str]


class ProductionRuntimeResponse(BaseModel):
    content: str
    provider: str
    model: str
    latency_ms: float
    cost_usd: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    attempted_providers: list[str]
    tool_results: list[str]
    cache_hit: bool
    input_guardrail: GuardrailStageResponse
    output_guardrail: GuardrailStageResponse
    evaluation: RuntimeEvaluationResponse


class ProductionReadinessResponse(BaseModel):
    status: str
    capabilities: dict[str, bool]
    providers: list[str]
