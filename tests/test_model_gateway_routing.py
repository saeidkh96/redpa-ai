import pytest

from app.model_gateway.contracts import LLMCapability
from app.model_gateway.providers.mock import MockLLMProvider
from app.model_gateway.registry import LLMProviderRegistry
from app.model_gateway.routing import (
    AgentRoutingStrategy,
    CompositeRoutingStrategy,
    ExplicitRoutingStrategy,
    ModelRoute,
    RoutingContext,
    CapabilityRoutingStrategy,
)


def _registry() -> LLMProviderRegistry:
    registry = LLMProviderRegistry(
        default_provider="primary",
    )
    registry.register(
        MockLLMProvider(
            name="primary",
            model="model-a",
        )
    )
    registry.register(
        MockLLMProvider(
            name="fallback",
            model="model-b",
        )
    )
    return registry


def test_explicit_provider_wins() -> None:
    strategy = CompositeRoutingStrategy(
        (
            ExplicitRoutingStrategy(),
            CapabilityRoutingStrategy(),
        )
    )

    route = strategy.select(
        registry=_registry(),
        context=RoutingContext(
            requested_provider="fallback",
        ),
    )

    assert route.provider == "fallback"
    assert route.reason == "explicit"


def test_agent_route_selects_provider_and_model() -> None:
    strategy = CompositeRoutingStrategy(
        (
            AgentRoutingStrategy(
                {
                    "research-agent": ModelRoute(
                        provider="fallback",
                        model="research-model",
                        reason="agent",
                    ),
                }
            ),
            CapabilityRoutingStrategy(),
        )
    )

    route = strategy.select(
        registry=_registry(),
        context=RoutingContext(
            agent_id="research-agent",
        ),
    )

    assert route.provider == "fallback"
    assert route.model == "research-model"


def test_capability_route_uses_default_provider() -> None:
    strategy = CompositeRoutingStrategy(
        (CapabilityRoutingStrategy(),)
    )

    route = strategy.select(
        registry=_registry(),
        context=RoutingContext(
            required_capability=LLMCapability.CHAT,
        ),
    )

    assert route.provider == "primary"
    assert route.reason == "default_capability"
