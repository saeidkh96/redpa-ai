import pytest
from app.model_gateway.config import ModelGatewayConfig, ProviderConfig
from app.model_gateway.contracts import LLMCapability
from app.model_gateway.factory import LLMProviderFactory, UnknownProviderTypeError
from app.model_gateway.providers.mock import MockLLMProvider
from app.model_gateway.providers.ollama import OllamaProvider
from app.model_gateway.registry import DuplicateProviderError, LLMProviderRegistry, ProviderNotFoundError


def test_factory_creates_ollama_adapter() -> None:
    provider = LLMProviderFactory().create(ProviderConfig(name="ollama", provider_type="ollama", base_url="http://localhost:11434", default_model="qwen2.5:7b"))
    assert isinstance(provider, OllamaProvider)


def test_factory_rejects_unknown_provider() -> None:
    with pytest.raises(UnknownProviderTypeError):
        LLMProviderFactory().create(ProviderConfig(name="x", provider_type="unknown", base_url="http://x", default_model="x"))


def test_registry_default_provider() -> None:
    registry = LLMProviderRegistry(default_provider="primary")
    provider = MockLLMProvider(name="primary")
    registry.register(provider)
    assert registry.get() is provider


def test_registry_rejects_duplicate() -> None:
    registry = LLMProviderRegistry(default_provider="mock")
    registry.register(MockLLMProvider())
    with pytest.raises(DuplicateProviderError):
        registry.register(MockLLMProvider())


def test_registry_filters_capabilities() -> None:
    registry = LLMProviderRegistry(default_provider="mock")
    registry.register(MockLLMProvider())
    assert len(registry.providers_supporting(LLMCapability.CHAT)) == 1


def test_registry_from_config_skips_disabled() -> None:
    config = ModelGatewayConfig(default_provider="a", providers=(
        ProviderConfig(name="a", provider_type="mock", base_url="http://x", default_model="a", enabled=True),
        ProviderConfig(name="b", provider_type="mock", base_url="http://x", default_model="b", enabled=False),
    ))
    registry = LLMProviderRegistry.from_config(config)
    assert len(registry) == 1
    assert "a" in registry
    assert "b" not in registry


def test_registry_requires_enabled_default() -> None:
    config = ModelGatewayConfig(default_provider="missing", providers=(ProviderConfig(name="a", provider_type="mock", base_url="http://x", default_model="a"),))
    with pytest.raises(ProviderNotFoundError):
        LLMProviderRegistry.from_config(config)
