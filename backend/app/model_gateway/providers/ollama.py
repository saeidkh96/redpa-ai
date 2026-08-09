from __future__ import annotations

from typing import Any
import httpx

from app.model_gateway.config import ProviderConfig
from app.model_gateway.contracts import LLMCapability, LLMProvider, LLMProviderError, LLMProviderHealth, LLMRequest, LLMResponse, LLMUsage, ProviderDescriptor


class OllamaProvider(LLMProvider):
    def __init__(self, config: ProviderConfig, *, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.config = config
        self._transport = transport
        self._descriptor = ProviderDescriptor(
            name=config.name,
            provider_type=config.provider_type,
            default_model=config.default_model,
            capabilities=frozenset({LLMCapability.CHAT, LLMCapability.JSON_OUTPUT, LLMCapability.STREAMING}),
            enabled=config.enabled,
        )

    @property
    def descriptor(self) -> ProviderDescriptor:
        return self._descriptor

    async def generate(self, request: LLMRequest) -> LLMResponse:
        model = request.model or self.config.default_model
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "stream": False,
        }
        options: dict[str, Any] = {}
        if request.temperature is not None:
            options["temperature"] = request.temperature
        if request.max_tokens is not None:
            options["num_predict"] = request.max_tokens
        if options:
            payload["options"] = options
        if request.response_format is not None:
            payload["format"] = request.response_format

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds, transport=self._transport) as client:
                response = await client.post(f"{self.config.base_url}/api/chat", json=payload)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise LLMProviderError("Ollama request timed out.", provider=self.config.name, retryable=True) from exc
        except httpx.ConnectError as exc:
            raise LLMProviderError("Could not connect to Ollama.", provider=self.config.name, retryable=True) from exc
        except httpx.HTTPStatusError as exc:
            raise LLMProviderError(
                f"Ollama returned HTTP {exc.response.status_code}.",
                provider=self.config.name,
                retryable=exc.response.status_code >= 500,
                status_code=exc.response.status_code,
            ) from exc

        try:
            data = response.json()
            content = data["message"]["content"]
        except (ValueError, KeyError, TypeError) as exc:
            raise LLMProviderError("Ollama returned an invalid chat response.", provider=self.config.name) from exc

        input_tokens = data.get("prompt_eval_count")
        output_tokens = data.get("eval_count")
        total_tokens = None
        if isinstance(input_tokens, int) or isinstance(output_tokens, int):
            total_tokens = (input_tokens or 0) + (output_tokens or 0)

        return LLMResponse(
            provider=self.config.name,
            model=str(data.get("model") or model),
            content=str(content),
            finish_reason=str(data.get("done_reason") or "") or None,
            usage=LLMUsage(
                input_tokens=input_tokens if isinstance(input_tokens, int) else None,
                output_tokens=output_tokens if isinstance(output_tokens, int) else None,
                total_tokens=total_tokens,
            ),
            raw=data,
        )

    async def health_check(self) -> LLMProviderHealth:
        try:
            async with httpx.AsyncClient(timeout=min(self.config.timeout_seconds, 10.0), transport=self._transport) as client:
                response = await client.get(f"{self.config.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
            models = tuple(str(item.get("name")) for item in data.get("models", []) if isinstance(item, dict) and item.get("name"))
            return LLMProviderHealth(provider=self.config.name, available=True, models=models)
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            return LLMProviderHealth(provider=self.config.name, available=False, detail=str(exc))
