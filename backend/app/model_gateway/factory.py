from __future__ import annotations

from collections.abc import Callable
from app.model_gateway.config import ProviderConfig
from app.model_gateway.contracts import LLMProvider
from app.model_gateway.providers.mock import MockLLMProvider
from app.model_gateway.providers.ollama import OllamaProvider
from app.model_gateway.providers.openai_compatible import OpenAICompatibleProvider
from app.model_gateway.providers.anthropic import AnthropicProvider
from app.model_gateway.providers.gemini import GeminiProvider

ProviderBuilder = Callable[[ProviderConfig], LLMProvider]


class UnknownProviderTypeError(ValueError):
    pass


class LLMProviderFactory:
    def __init__(self) -> None:
        self._builders: dict[str, ProviderBuilder] = {
            "ollama": lambda c: OllamaProvider(c),
            "openai_compatible": lambda c: OpenAICompatibleProvider(c),
            "anthropic": lambda c: AnthropicProvider(c),
            "gemini": lambda c: GeminiProvider(c),
            "mock": lambda c: MockLLMProvider(name=c.name, model=c.default_model),
        }

    def register_builder(self, provider_type: str, builder: ProviderBuilder) -> None:
        key = provider_type.strip().lower()
        if not key:
            raise ValueError("provider_type cannot be empty.")
        self._builders[key] = builder

    def create(self, config: ProviderConfig) -> LLMProvider:
        key = config.provider_type.strip().lower()
        try:
            builder = self._builders[key]
        except KeyError as exc:
            raise UnknownProviderTypeError(f"Unsupported LLM provider type: {config.provider_type}") from exc
        return builder(config)
