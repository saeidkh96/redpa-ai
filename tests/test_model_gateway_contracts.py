import pytest
from app.model_gateway.contracts import LLMCapability, LLMMessage, LLMRequest
from app.model_gateway.providers.mock import MockLLMProvider


def test_request_requires_messages() -> None:
    with pytest.raises(ValueError):
        LLMRequest(messages=())


def test_request_validates_temperature() -> None:
    with pytest.raises(ValueError):
        LLMRequest(messages=(LLMMessage(role="user", content="hello"),), temperature=3.0)


@pytest.mark.asyncio
async def test_mock_provider_contract() -> None:
    provider = MockLLMProvider(content="hello from mock")
    response = await provider.generate(LLMRequest(messages=(LLMMessage(role="user", content="hello"),)))
    assert response.provider == "mock"
    assert response.content == "hello from mock"
    assert provider.supports(LLMCapability.CHAT)
