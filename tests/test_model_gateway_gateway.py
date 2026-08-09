import pytest

from app.model_gateway.contracts import (
    LLMMessage,
    LLMProviderError,
    LLMRequest,
)
from app.model_gateway.gateway import ModelGateway
from app.model_gateway.providers.mock import MockLLMProvider
from app.model_gateway.registry import LLMProviderRegistry
from app.model_gateway.reliability import (
    ReliableProviderExecutor,
    ReliabilityPolicy,
)
from app.model_gateway.routing import (
    CompositeRoutingStrategy,
    ExplicitRoutingStrategy,
    ModelRoute,
    RoutingContext,
)


class FailingProvider(MockLLMProvider):
    async def generate(self, request):
        raise LLMProviderError(
            "temporary",
            provider=self.descriptor.name,
            retryable=True,
        )


class StaticRoute:
    def __init__(self, route: ModelRoute) -> None:
        self.route = route

    def select(self, *, registry, context):
        return self.route


@pytest.mark.asyncio
async def test_gateway_falls_back_after_retryable_failure() -> None:
    registry = LLMProviderRegistry(
        default_provider="primary",
    )
    registry.register(
        FailingProvider(
            name="primary",
            model="model-a",
        )
    )
    registry.register(
        MockLLMProvider(
            name="fallback",
            model="model-b",
            content="fallback response",
        )
    )

    gateway = ModelGateway(
        registry=registry,
        router=CompositeRoutingStrategy(
            (
                StaticRoute(
                    ModelRoute(
                        provider="primary",
                        model="model-a",
                        fallback_providers=("fallback",),
                    )
                ),
            )
        ),
        executor=ReliableProviderExecutor(
            policy=ReliabilityPolicy(
                attempts=1,
                timeout_seconds=2.0,
                retry_backoff_seconds=0.0,
            )
        ),
    )

    result = await gateway.invoke(
        request=LLMRequest(
            messages=(
                LLMMessage(
                    role="user",
                    content="hello",
                ),
            ),
        )
    )

    assert result.response.provider == "fallback"
    assert result.response.content == "fallback response"
    assert result.attempted_providers == (
        "primary",
        "fallback",
    )
