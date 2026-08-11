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


class AnthropicProvider(LLMProvider):
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

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "x-api-key": self.config.api_key or "",
            "anthropic-version": "2023-06-01",
        }

    async def generate(self, request: LLMRequest) -> LLMResponse:
        model = request.model or self.config.default_model
        system_parts = [m.content for m in request.messages if m.role == "system"]
        messages = [
            {"role": m.role if m.role in {"user", "assistant"} else "user", "content": m.content}
            for m in request.messages if m.role != "system"
        ]
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": request.max_tokens or 1024,
        }
        if system_parts:
            payload["system"] = "\n\n".join(system_parts)
        if request.temperature is not None:
            payload["temperature"] = request.temperature

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds, transport=self._transport) as client:
                response = await client.post(f"{self.config.base_url}/v1/messages", headers=self._headers(), json=payload)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise LLMProviderError("Anthropic request timed out.", provider=self.config.name, retryable=True) from exc
        except httpx.ConnectError as exc:
            raise LLMProviderError("Could not connect to Anthropic.", provider=self.config.name, retryable=True) from exc
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            raise LLMProviderError(
                f"Anthropic returned HTTP {code}.",
                provider=self.config.name,
                retryable=code in {408, 409, 429} or code >= 500,
                status_code=code,
            ) from exc

        try:
            data = response.json()
            content_blocks = data.get("content", [])
            text = "\n".join(str(block.get("text", "")) for block in content_blocks if isinstance(block, dict) and block.get("type") == "text")
        except (ValueError, TypeError) as exc:
            raise LLMProviderError("Anthropic returned an invalid response.", provider=self.config.name) from exc
        usage = data.get("usage") or {}
        inp = usage.get("input_tokens")
        out = usage.get("output_tokens")
        total = (inp or 0) + (out or 0) if isinstance(inp, int) or isinstance(out, int) else None
        return LLMResponse(
            provider=self.config.name,
            model=str(data.get("model") or model),
            content=text,
            finish_reason=data.get("stop_reason"),
            usage=LLMUsage(input_tokens=inp, output_tokens=out, total_tokens=total),
            raw=data,
        )

    async def health_check(self) -> LLMProviderHealth:
        if not self.config.api_key:
            return LLMProviderHealth(provider=self.config.name, available=False, detail="ANTHROPIC_API_KEY is not configured.")
        return LLMProviderHealth(provider=self.config.name, available=True, models=(self.config.default_model,), detail="credential configured")
