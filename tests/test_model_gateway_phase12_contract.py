from app.model_gateway.bootstrap import build_model_gateway
from app.model_gateway.config import ModelGatewayConfig, ProviderConfig
from app.model_gateway.contracts import (
    LLMCapability,
    LLMMessage,
    LLMRequest,
)
from app.model_gateway.providers.mock import MockLLMProvider
from app.model_gateway.registry import LLMProviderRegistry
from app.model_gateway.routing import CompositeRoutingStrategy


def test_phase12_gateway_has_provider_neutral_contract() -> None:
    request = LLMRequest(
        messages=(
            LLMMessage(
                role="user",
                content="hello",
            ),
        ),
    )

    assert request.messages[0].role == "user"


def test_phase12_registry_can_host_multiple_providers() -> None:
    registry = LLMProviderRegistry(
        default_provider="a",
    )
    registry.register(
        MockLLMProvider(
            name="a",
            model="model-a",
        ),
    )
    registry.register(
        MockLLMProvider(
            name="b",
            model="model-b",
        ),
    )

    assert len(registry) == 2
    assert len(
        registry.providers_supporting(
            LLMCapability.CHAT,
        ),
    ) == 2


def test_phase12_default_gateway_builds_from_config(monkeypatch) -> None:
    monkeypatch.setenv(
        "MODEL_GATEWAY_DEFAULT_PROVIDER",
        "ollama",
    )
    monkeypatch.setenv(
        "MODEL_GATEWAY_OLLAMA_ENABLED",
        "true",
    )
    monkeypatch.setenv(
        "MODEL_GATEWAY_OPENAI_COMPATIBLE_ENABLED",
        "false",
    )

    gateway = build_model_gateway()

    assert gateway.registry.get().descriptor.name == "ollama"


def test_phase12_agent_route_environment(monkeypatch) -> None:
    monkeypatch.setenv(
        "MODEL_GATEWAY_AGENT_ROUTES_JSON",
        '{"research-agent":{"provider":"ollama","model":"qwen2.5:7b"}}',
    )

    registry = LLMProviderRegistry(
        default_provider="ollama",
    )
    registry.register(
        MockLLMProvider(
            name="ollama",
            model="qwen2.5:7b",
        )
    )

    router = CompositeRoutingStrategy.from_environment()
    route = router.select(
        registry=registry,
        context=__import__(
            "app.model_gateway.routing",
            fromlist=["RoutingContext"],
        ).RoutingContext(
            agent_id="research-agent",
        ),
    )

    assert route.provider == "ollama"
    assert route.model == "qwen2.5:7b"
    assert route.reason == "agent"
