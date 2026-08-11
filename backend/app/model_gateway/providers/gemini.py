from __future__ import annotations

from typing import Any
import httpx

from app.model_gateway.config import ProviderConfig
from app.model_gateway.contracts import (
    LLMCapability,
    LLMProvider,
    LLMProviderError,
    LLMProviderHealth,
    LLMRequest,
    LLMResponse,
    LLMUsage,
    ProviderDescriptor,
)


class GeminiProvider(LLMProvider):
    def __init__(self, config: ProviderConfig, *, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.config = config
        self._transport = transport
        self._descriptor = ProviderDescriptor(
            name=config.name,
            provider_type=config.provider_type,
            default_model=config.default_model,
            capabilities=frozenset({LLMCapability.CHAT, LLMCapability.JSON_OUTPUT, LLMCapability.TOOLS, LLMCapability.VISION}),
            enabled=config.enabled,
        )

    @property
    def descriptor(self) -> ProviderDescriptor:
        return self._descriptor

    async def generate(self, request: LLMRequest) -> LLMResponse:
        if not self.config.api_key:
            raise LLMProviderError("Gemini API key is not configured.", provider=self.config.name)
        model = request.model or self.config.default_model
        contents = []
        for message in request.messages:
            role = "model" if message.role == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": message.content}]})
        generation: dict[str, Any] = {}
        if request.temperature is not None:
            generation["temperature"] = request.temperature
        if request.max_tokens is not None:
            generation["maxOutputTokens"] = request.max_tokens
        if request.response_format == "json":
            generation["responseMimeType"] = "application/json"
        payload: dict[str, Any] = {"contents": contents}
        if generation:
            payload["generationConfig"] = generation
        url = f"{self.config.base_url}/v1beta/models/{model}:generateContent"
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds, transport=self._transport) as client:
                response = await client.post(url, params={"key": self.config.api_key}, json=payload)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise LLMProviderError("Gemini request timed out.", provider=self.config.name, retryable=True) from exc
        except httpx.ConnectError as exc:
            raise LLMProviderError("Could not connect to Gemini.", provider=self.config.name, retryable=True) from exc
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            raise LLMProviderError(f"Gemini returned HTTP {code}.", provider=self.config.name, retryable=code in {408, 429} or code >= 500, status_code=code) from exc
        try:
            data = response.json()
            candidate = data["candidates"][0]
            text = "\n".join(str(p.get("text", "")) for p in candidate["content"].get("parts", []) if isinstance(p, dict))
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError("Gemini returned an invalid response.", provider=self.config.name) from exc
        usage = data.get("usageMetadata") or {}
        inp = usage.get("promptTokenCount")
        out = usage.get("candidatesTokenCount")
        total = usage.get("totalTokenCount")
        return LLMResponse(provider=self.config.name, model=model, content=text, finish_reason=candidate.get("finishReason"), usage=LLMUsage(input_tokens=inp, output_tokens=out, total_tokens=total), raw=data)

    async def health_check(self) -> LLMProviderHealth:
        if not self.config.api_key:
            return LLMProviderHealth(provider=self.config.name, available=False, detail="GEMINI_API_KEY is not configured.")
        return LLMProviderHealth(provider=self.config.name, available=True, models=(self.config.default_model,), detail="credential configured")
