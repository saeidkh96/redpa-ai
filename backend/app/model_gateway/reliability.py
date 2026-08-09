from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from enum import Enum

from app.model_gateway.contracts import (
    LLMProvider,
    LLMProviderError,
    LLMRequest,
    LLMResponse,
)


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass(slots=True)
class CircuitBreaker:
    failure_threshold: int = 3
    recovery_timeout_seconds: float = 30.0

    _failures: int = 0
    _opened_at: float | None = None
    _state: CircuitState = CircuitState.CLOSED

    @property
    def state(self) -> CircuitState:
        if (
            self._state == CircuitState.OPEN
            and self._opened_at is not None
            and time.monotonic() - self._opened_at
            >= self.recovery_timeout_seconds
        ):
            self._state = CircuitState.HALF_OPEN

        return self._state

    def allow_request(self) -> bool:
        return self.state != CircuitState.OPEN

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None
        self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self._failures += 1

        if self._failures >= self.failure_threshold:
            self._state = CircuitState.OPEN
            self._opened_at = time.monotonic()

    def snapshot(self) -> dict[str, object]:
        return {
            "state": self.state.value,
            "failures": self._failures,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout_seconds": self.recovery_timeout_seconds,
        }


class CircuitOpenError(LLMProviderError):
    pass


@dataclass(frozen=True, slots=True)
class ReliabilityPolicy:
    attempts: int = 2
    timeout_seconds: float = 120.0
    retry_backoff_seconds: float = 0.25

    def __post_init__(self) -> None:
        if self.attempts < 1:
            raise ValueError("attempts must be at least 1.")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero.")
        if self.retry_backoff_seconds < 0:
            raise ValueError(
                "retry_backoff_seconds cannot be negative.",
            )


class ReliableProviderExecutor:
    """Retry + timeout + circuit-breaker execution wrapper."""

    def __init__(
        self,
        *,
        policy: ReliabilityPolicy | None = None,
    ) -> None:
        self.policy = policy or ReliabilityPolicy()
        self._breakers: dict[str, CircuitBreaker] = {}

    def breaker_for(self, provider_name: str) -> CircuitBreaker:
        return self._breakers.setdefault(
            provider_name,
            CircuitBreaker(),
        )

    async def execute(
        self,
        *,
        provider: LLMProvider,
        request: LLMRequest,
    ) -> LLMResponse:
        provider_name = provider.descriptor.name
        breaker = self.breaker_for(provider_name)

        if not breaker.allow_request():
            raise CircuitOpenError(
                f"Circuit breaker is open for provider {provider_name!r}.",
                provider=provider_name,
                retryable=True,
            )

        last_error: LLMProviderError | None = None

        for attempt in range(1, self.policy.attempts + 1):
            try:
                response = await asyncio.wait_for(
                    provider.generate(request),
                    timeout=self.policy.timeout_seconds,
                )
                breaker.record_success()
                return response

            except asyncio.TimeoutError as exc:
                last_error = LLMProviderError(
                    f"Provider {provider_name!r} timed out.",
                    provider=provider_name,
                    retryable=True,
                )
                breaker.record_failure()

                if attempt >= self.policy.attempts:
                    raise last_error from exc

            except LLMProviderError as exc:
                last_error = exc
                breaker.record_failure()

                if not exc.retryable or attempt >= self.policy.attempts:
                    raise

            if self.policy.retry_backoff_seconds:
                await asyncio.sleep(
                    self.policy.retry_backoff_seconds * attempt,
                )

        assert last_error is not None
        raise last_error

    def circuit_snapshot(self) -> dict[str, dict[str, object]]:
        return {
            provider: breaker.snapshot()
            for provider, breaker in self._breakers.items()
        }
