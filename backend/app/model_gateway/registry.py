from __future__ import annotations

from app.model_gateway.config import ModelGatewayConfig
from app.model_gateway.contracts import LLMCapability, LLMProvider, LLMProviderHealth, ProviderDescriptor
from app.model_gateway.factory import LLMProviderFactory


class ProviderNotFoundError(KeyError):
    pass


class DuplicateProviderError(ValueError):
    pass


class LLMProviderRegistry:
    def __init__(self, *, default_provider: str) -> None:
        self.default_provider = default_provider
        self._providers: dict[str, LLMProvider] = {}

    @classmethod
    def from_config(cls, config: ModelGatewayConfig, *, factory: LLMProviderFactory | None = None) -> "LLMProviderRegistry":
        factory = factory or LLMProviderFactory()
        registry = cls(default_provider=config.default_provider)
        for provider_config in config.providers:
            if provider_config.enabled:
                registry.register(factory.create(provider_config))
        if registry._providers and registry.default_provider not in registry._providers:
            raise ProviderNotFoundError(f"Configured default provider {registry.default_provider!r} is not enabled.")
        return registry

    def register(self, provider: LLMProvider, *, replace: bool = False) -> None:
        name = provider.descriptor.name
        if name in self._providers and not replace:
            raise DuplicateProviderError(f"Provider {name!r} is already registered.")
        self._providers[name] = provider

    def get(self, name: str | None = None) -> LLMProvider:
        target = name or self.default_provider
        try:
            return self._providers[target]
        except KeyError as exc:
            raise ProviderNotFoundError(f"Provider {target!r} is not registered.") from exc

    def descriptors(self) -> list[ProviderDescriptor]:
        return [p.descriptor for p in self._providers.values()]

    def providers_supporting(self, capability: LLMCapability) -> list[LLMProvider]:
        return [p for p in self._providers.values() if p.supports(capability)]

    async def health(self) -> list[LLMProviderHealth]:
        return [await p.health_check() for p in self._providers.values()]

    def __len__(self) -> int:
        return len(self._providers)

    def __contains__(self, name: object) -> bool:
        return name in self._providers
