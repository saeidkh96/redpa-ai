from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class CacheEntry:
    value: Any
    expires_at: float


class TTLCache:
    def __init__(self, *, max_entries: int = 256) -> None:
        self.max_entries = max_entries
        self._entries: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            if entry.expires_at <= time.monotonic():
                self._entries.pop(key, None)
                return None
            return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        *,
        ttl_seconds: float,
    ) -> None:
        if ttl_seconds <= 0:
            return

        async with self._lock:
            if len(self._entries) >= self.max_entries:
                oldest_key = min(
                    self._entries,
                    key=lambda item: self._entries[item].expires_at,
                )
                self._entries.pop(oldest_key, None)

            self._entries[key] = CacheEntry(
                value=value,
                expires_at=time.monotonic() + ttl_seconds,
            )


class TokenBucketRateLimiter:
    def __init__(
        self,
        *,
        rate_per_second: float = 5.0,
        capacity: float = 10.0,
    ) -> None:
        self.rate_per_second = rate_per_second
        self.capacity = capacity
        self.tokens = capacity
        self.updated_at = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        while True:
            async with self._lock:
                now = time.monotonic()
                elapsed = now - self.updated_at
                self.updated_at = now

                self.tokens = min(
                    self.capacity,
                    self.tokens + elapsed * self.rate_per_second,
                )

                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return

                wait_seconds = (
                    1.0 - self.tokens
                ) / self.rate_per_second

            await asyncio.sleep(wait_seconds)


class CircuitBreakerOpenError(Exception):
    pass


class CircuitBreaker:
    def __init__(
        self,
        *,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 30.0,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.failure_count = 0
        self.opened_at: float | None = None
        self._lock = asyncio.Lock()

    async def before_request(self) -> None:
        async with self._lock:
            if self.opened_at is None:
                return

            if (
                time.monotonic() - self.opened_at
                >= self.recovery_timeout_seconds
            ):
                self.opened_at = None
                self.failure_count = 0
                return

            raise CircuitBreakerOpenError(
                "External service circuit breaker is open."
            )

    async def record_success(self) -> None:
        async with self._lock:
            self.failure_count = 0
            self.opened_at = None

    async def record_failure(self) -> None:
        async with self._lock:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.opened_at = time.monotonic()
