from __future__ import annotations

from typing import Any
import httpx

from app.model_gateway.config import ProviderConfig
from app.model_gateway.contracts import LLMCapability, LLMProvider, LLMProviderError, LLMProviderHealth, LLMRequest, LLMResponse, LLMUsage, ProviderDescriptor


class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, config: ProviderConfig, *, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.config = config
        self._transport = transport
        self._descriptor = ProviderDescriptor(
            name=config.name,
            provider_type=config.provider_type,
            default_model=config.default_model,
            capabilities=frozenset({LLMCapability.CHAT, LLMCapability.JSON_OUTPUT, LLMCapability.STREAMING, LLMCapability.TOOLS}),
            enabled=config.enabled,
        )

    @property
    def descriptor(self) -> ProviderDescriptor:
        return self._descriptor

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    async def generate(self, request: LLMRequest) -> LLMResponse:
        model = request.model or self.config.default_model
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if request.response_format is not None:
            payload["response_format"] = (
                {"type": "json_object"}
                if request.response_format == "json"
                else request.response_format
            )

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds, transport=self._transport) as client:
                response = await client.post(
                    f"{self.config.base_url}/v1/chat/completions",
                    headers=self._headers(),
                    json=payload,
                )
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise LLMProviderError("OpenAI-compatible request timed out.", provider=self.config.name, retryable=True) from exc
        except httpx.ConnectError as exc:
            raise LLMProviderError("Could not connect to OpenAI-compatible provider.", provider=self.config.name, retryable=True) from exc
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            raise LLMProviderError(
                f"OpenAI-compatible provider returned HTTP {code}.",
                provider=self.config.name,
                retryable=code in {408, 429} or code >= 500,
                status_code=code,
            ) from exc

        try:
            data = response.json()
            choice = data["choices"][0]
            content = choice["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError("OpenAI-compatible provider returned an invalid response.", provider=self.config.name) from exc

        usage = data.get("usage") or {}
        return LLMResponse(
            provider=self.config.name,
            model=str(data.get("model") or model),
            content=str(content or ""),
            finish_reason=choice.get("finish_reason"),
            usage=LLMUsage(
                input_tokens=usage.get("prompt_tokens"),
                output_tokens=usage.get("completion_tokens"),
                total_tokens=usage.get("total_tokens"),
            ),
            raw=data,
        )

    async def health_check(self) -> LLMProviderHealth:
        try:
            async with httpx.AsyncClient(timeout=min(self.config.timeout_seconds, 10.0), transport=self._transport) as client:
                response = await client.get(f"{self.config.base_url}/v1/models", headers=self._headers())
                response.raise_for_status()
                data = response.json()
            models = tuple(str(item.get("id")) for item in data.get("data", []) if isinstance(item, dict) and item.get("id"))
            return LLMProviderHealth(provider=self.config.name, available=True, models=models)
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            return LLMProviderHealth(provider=self.config.name, available=False, detail=str(exc))
