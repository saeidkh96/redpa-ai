from __future__ import annotations

from app.model_gateway.contracts import LLMCapability, LLMProvider, LLMProviderHealth, LLMRequest, LLMResponse, LLMUsage, ProviderDescriptor


class MockLLMProvider(LLMProvider):
    def __init__(self, *, name: str = "mock", model: str = "mock-model", content: str = "mock response", available: bool = True) -> None:
        self._content = content
        self._available = available
        self._descriptor = ProviderDescriptor(
            name=name,
            provider_type="mock",
            default_model=model,
            capabilities=frozenset({LLMCapability.CHAT, LLMCapability.JSON_OUTPUT}),
        )

    @property
    def descriptor(self) -> ProviderDescriptor:
        return self._descriptor

    async def generate(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            provider=self.descriptor.name,
            model=request.model or self.descriptor.default_model,
            content=self._content,
            finish_reason="stop",
            usage=LLMUsage(input_tokens=1, output_tokens=1, total_tokens=2),
        )

    async def health_check(self) -> LLMProviderHealth:
        return LLMProviderHealth(
            provider=self.descriptor.name,
            available=self._available,
            models=(self.descriptor.default_model,),
        )
