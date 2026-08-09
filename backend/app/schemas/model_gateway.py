from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.model_gateway.contracts import LLMCapability


class GatewayMessage(BaseModel):
    role: str = Field(min_length=1, max_length=50)
    content: str = Field(min_length=1)


class GatewayInvokeRequest(BaseModel):
    messages: list[GatewayMessage] = Field(min_length=1)
    agent_id: str | None = Field(default=None, max_length=150)
    provider: str | None = Field(default=None, max_length=100)
    model: str | None = Field(default=None, max_length=200)
    capability: LLMCapability = LLMCapability.CHAT
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0)
    response_format: str | dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class GatewayRoutePreviewRequest(BaseModel):
    agent_id: str | None = Field(default=None, max_length=150)
    provider: str | None = Field(default=None, max_length=100)
    model: str | None = Field(default=None, max_length=200)
    capability: LLMCapability = LLMCapability.CHAT


class GatewayRouteResponse(BaseModel):
    provider: str
    model: str | None
    reason: str
    fallback_providers: list[str]


class GatewayUsageResponse(BaseModel):
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


class GatewayInvokeResponse(BaseModel):
    provider: str
    model: str
    content: str
    finish_reason: str | None = None
    usage: GatewayUsageResponse | None = None
    route: GatewayRouteResponse
    attempted_providers: list[str]


class ProviderDescriptorResponse(BaseModel):
    name: str
    provider_type: str
    default_model: str
    capabilities: list[str]
    enabled: bool


class ProviderHealthResponse(BaseModel):
    provider: str
    available: bool
    models: list[str]
    detail: str | None = None


class CircuitBreakerResponse(BaseModel):
    provider: str
    state: str
    failures: int
    failure_threshold: int
    recovery_timeout_seconds: float
