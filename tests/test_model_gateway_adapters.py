import json
import httpx
import pytest
from app.model_gateway.config import ProviderConfig
from app.model_gateway.contracts import LLMMessage, LLMRequest
from app.model_gateway.providers.ollama import OllamaProvider
from app.model_gateway.providers.openai_compatible import OpenAICompatibleProvider


@pytest.mark.asyncio
async def test_ollama_adapter_normalizes_response() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        return httpx.Response(200, json={"model":"qwen2.5:7b","message":{"role":"assistant","content":"ollama response"},"done_reason":"stop","prompt_eval_count":10,"eval_count":5})
    provider = OllamaProvider(ProviderConfig(name="ollama", provider_type="ollama", base_url="http://ollama.local", default_model="qwen2.5:7b"), transport=httpx.MockTransport(handler))
    response = await provider.generate(LLMRequest(messages=(LLMMessage(role="user", content="hello"),)))
    assert response.content == "ollama response"
    assert response.usage and response.usage.total_tokens == 15


@pytest.mark.asyncio
async def test_openai_compatible_adapter_normalizes_response() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-key"
        return httpx.Response(200, json={"model":"test-model","choices":[{"message":{"role":"assistant","content":"compatible response"},"finish_reason":"stop"}],"usage":{"prompt_tokens":7,"completion_tokens":3,"total_tokens":10}})
    provider = OpenAICompatibleProvider(ProviderConfig(name="compatible", provider_type="openai_compatible", base_url="http://provider.local", default_model="test-model", api_key="test-key"), transport=httpx.MockTransport(handler))
    response = await provider.generate(LLMRequest(messages=(LLMMessage(role="user", content="hello"),)))
    assert response.provider == "compatible"
    assert response.content == "compatible response"
    assert response.usage and response.usage.total_tokens == 10
