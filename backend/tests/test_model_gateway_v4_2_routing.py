from __future__ import annotations

import pytest

from app.model_gateway.contracts import (
    LLMCapability,
    LLMMessage,
    LLMProvider,
    LLMProviderError,
    LLMProviderHealth,
    LLMRequest,
    LLMResponse,
    LLMUsage,
    ProviderDescriptor,
)
from app.model_gateway.economics import (
    ModelEconomics,
    ModelEconomicsCatalog,
)
from app.model_gateway.gateway import ModelGateway
from app.model_gateway.providers.mock import MockLLMProvider
from app.model_gateway.registry import LLMProviderRegistry
from app.model_gateway.reliability import (
    ReliabilityPolicy,
    ReliableProviderExecutor,
)
from app.model_gateway.routing import (
    CompositeRoutingStrategy,
    CostAwareRoutingStrategy,
)


class RetryableFailingProvider(LLMProvider):
    """
    Test provider that always fails with a retryable provider error.

    This allows the gateway fallback path to be tested without making
    any external API calls.
    """

    def __init__(
        self,
        *,
        name: str,
        model: str,
    ) -> None:
        self.calls = 0

        self._descriptor = ProviderDescriptor(
            name=name,
            provider_type="test-failing",
            default_model=model,
            capabilities=frozenset(
                {
                    LLMCapability.CHAT,
                }
            ),
        )

    @property
    def descriptor(self) -> ProviderDescriptor:
        return self._descriptor

    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        self.calls += 1

        raise LLMProviderError(
            "Simulated retryable provider failure.",
            provider=self.descriptor.name,
            retryable=True,
            status_code=503,
        )

    async def health_check(self) -> LLMProviderHealth:
        return LLMProviderHealth(
            provider=self.descriptor.name,
            available=False,
            models=(self.descriptor.default_model,),
            detail="Simulated provider failure.",
        )


def build_gateway(
    *,
    cheap_provider: LLMProvider,
    expensive_provider: LLMProvider,
) -> ModelGateway:
    registry = LLMProviderRegistry(
        default_provider=cheap_provider.descriptor.name,
    )

    registry.register(cheap_provider)
    registry.register(expensive_provider)

    economics = ModelEconomicsCatalog(
        entries={
            "cheap-provider:cheap-model": ModelEconomics(
                provider="cheap-provider",
                model="cheap-model",
                input_per_1k=0.001,
                output_per_1k=0.002,
            ),
            "expensive-provider:expensive-model": ModelEconomics(
                provider="expensive-provider",
                model="expensive-model",
                input_per_1k=0.020,
                output_per_1k=0.040,
            ),
        }
    )

    router = CompositeRoutingStrategy(
        (
            CostAwareRoutingStrategy(
                catalog=economics,
            ),
        )
    )

    executor = ReliableProviderExecutor(
        policy=ReliabilityPolicy(
            attempts=1,
            timeout_seconds=5.0,
            retry_backoff_seconds=0.0,
        )
    )

    return ModelGateway(
        registry=registry,
        router=router,
        executor=executor,
    )


def build_request() -> LLMRequest:
    return LLMRequest(
        messages=(
            LLMMessage(
                role="user",
                content="Production routing validation.",
            ),
        ),
        max_tokens=100,
        metadata={
            "routing_mode": "cost",
            "estimated_input_tokens": 1000,
            "estimated_output_tokens": 500,
        },
    )


def test_cost_aware_routing_selects_cheapest_provider() -> None:
    cheap = MockLLMProvider(
        name="cheap-provider",
        model="cheap-model",
        content="cheap response",
    )

    expensive = MockLLMProvider(
        name="expensive-provider",
        model="expensive-model",
        content="expensive response",
    )

    gateway = build_gateway(
        cheap_provider=cheap,
        expensive_provider=expensive,
    )

    route = gateway.preview_route(
        agent_id="enterprise-support-agent",
        capability=LLMCapability.CHAT,
        metadata={
            "routing_mode": "cost",
            "estimated_input_tokens": 1000,
            "estimated_output_tokens": 500,
        },
    )

    assert route.provider == "cheap-provider"
    assert route.model == "cheap-model"
    assert route.reason == "cost_aware"

    assert route.fallback_providers == (
        "expensive-provider",
    )


@pytest.mark.asyncio
async def test_retryable_primary_failure_uses_fallback_provider() -> None:
    cheap = RetryableFailingProvider(
        name="cheap-provider",
        model="cheap-model",
    )

    expensive = MockLLMProvider(
        name="expensive-provider",
        model="expensive-model",
        content="fallback response",
    )

    gateway = build_gateway(
        cheap_provider=cheap,
        expensive_provider=expensive,
    )

    result = await gateway.invoke(
        request=build_request(),
        agent_id="enterprise-support-agent",
        capability=LLMCapability.CHAT,
    )

    assert cheap.calls == 1

    assert result.route.provider == "cheap-provider"
    assert result.route.reason == "cost_aware"

    assert result.response.provider == "expensive-provider"
    assert result.response.model == "expensive-model"
    assert result.response.content == "fallback response"

    assert result.attempted_providers == (
        "cheap-provider",
        "expensive-provider",
    )


@pytest.mark.asyncio
async def test_tenant_provider_governance_filters_primary_provider() -> None:
    cheap = RetryableFailingProvider(
        name="cheap-provider",
        model="cheap-model",
    )

    expensive = MockLLMProvider(
        name="expensive-provider",
        model="expensive-model",
        content="governed fallback response",
    )

    gateway = build_gateway(
        cheap_provider=cheap,
        expensive_provider=expensive,
    )

    result = await gateway.invoke(
        request=build_request(),
        agent_id="enterprise-support-agent",
        capability=LLMCapability.CHAT,
        allowed_providers={
            "expensive-provider",
        },
    )

    # The cheapest provider was selected by routing,
    # but tenant governance prevented it from executing.
    assert cheap.calls == 0

    assert result.route.provider == "cheap-provider"

    assert result.response.provider == "expensive-provider"
    assert result.response.content == "governed fallback response"

    assert result.attempted_providers == (
        "expensive-provider",
    )


@pytest.mark.asyncio
async def test_successful_cheapest_provider_does_not_use_fallback() -> None:
    cheap = MockLLMProvider(
        name="cheap-provider",
        model="cheap-model",
        content="primary response",
    )

    expensive = MockLLMProvider(
        name="expensive-provider",
        model="expensive-model",
        content="fallback response",
    )

    gateway = build_gateway(
        cheap_provider=cheap,
        expensive_provider=expensive,
    )

    result = await gateway.invoke(
        request=build_request(),
        agent_id="enterprise-support-agent",
        capability=LLMCapability.CHAT,
    )

    assert result.response.provider == "cheap-provider"
    assert result.response.model == "cheap-model"
    assert result.response.content == "primary response"

    assert result.attempted_providers == (
        "cheap-provider",
    )


@pytest.mark.asyncio
async def test_retryable_failure_updates_circuit_breaker() -> None:
    cheap = RetryableFailingProvider(
        name="cheap-provider",
        model="cheap-model",
    )

    expensive = MockLLMProvider(
        name="expensive-provider",
        model="expensive-model",
        content="fallback response",
    )

    gateway = build_gateway(
        cheap_provider=cheap,
        expensive_provider=expensive,
    )

    await gateway.invoke(
        request=build_request(),
        capability=LLMCapability.CHAT,
    )

    snapshot = gateway.executor.circuit_snapshot()

    assert "cheap-provider" in snapshot

    assert snapshot["cheap-provider"]["failures"] == 1
    assert snapshot["cheap-provider"]["state"] == "closed"

    assert "expensive-provider" in snapshot
    assert snapshot["expensive-provider"]["failures"] == 0
    assert snapshot["expensive-provider"]["state"] == "closed"
