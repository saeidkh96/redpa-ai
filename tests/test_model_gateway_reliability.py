import pytest

from app.model_gateway.contracts import (
    LLMMessage,
    LLMProviderError,
    LLMRequest,
)
from app.model_gateway.providers.mock import MockLLMProvider
from app.model_gateway.reliability import (
    CircuitState,
    ReliableProviderExecutor,
    ReliabilityPolicy,
)


class FlakyProvider(MockLLMProvider):
    def __init__(self) -> None:
        super().__init__(
            name="flaky",
            model="flaky-model",
        )
        self.calls = 0

    async def generate(self, request):
        self.calls += 1
        if self.calls == 1:
            raise LLMProviderError(
                "temporary",
                provider="flaky",
                retryable=True,
            )
        return await super().generate(request)


@pytest.mark.asyncio
async def test_retry_recovers_from_retryable_failure() -> None:
    provider = FlakyProvider()
    executor = ReliableProviderExecutor(
        policy=ReliabilityPolicy(
            attempts=2,
            timeout_seconds=2.0,
            retry_backoff_seconds=0.0,
        )
    )

    response = await executor.execute(
        provider=provider,
        request=LLMRequest(
            messages=(
                LLMMessage(
                    role="user",
                    content="hello",
                ),
            ),
        ),
    )

    assert response.content == "mock response"
    assert provider.calls == 2
    assert executor.breaker_for("flaky").state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_non_retryable_failure_is_not_retried() -> None:
    class FatalProvider(MockLLMProvider):
        def __init__(self) -> None:
            super().__init__(name="fatal")
            self.calls = 0

        async def generate(self, request):
            self.calls += 1
            raise LLMProviderError(
                "fatal",
                provider="fatal",
                retryable=False,
            )

    provider = FatalProvider()
    executor = ReliableProviderExecutor(
        policy=ReliabilityPolicy(
            attempts=3,
            timeout_seconds=2.0,
            retry_backoff_seconds=0.0,
        )
    )

    with pytest.raises(LLMProviderError):
        await executor.execute(
            provider=provider,
            request=LLMRequest(
                messages=(
                    LLMMessage(
                        role="user",
                        content="hello",
                    ),
                ),
            ),
        )

    assert provider.calls == 1
