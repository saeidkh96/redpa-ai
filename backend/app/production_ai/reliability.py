from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any


class AsyncConcurrencyGate:
    def __init__(self, limit: int = 32) -> None:
        if limit < 1:
            raise ValueError("limit must be >= 1")
        self._sem = asyncio.Semaphore(limit)

    async def __aenter__(self):
        await self._sem.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self._sem.release()


class InMemoryIdempotencyStore:
    def __init__(self, ttl_seconds: float = 300.0) -> None:
        self.ttl_seconds = ttl_seconds
        self._values: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        item = self._values.get(key)
        if item is None:
            return None
        expires, value = item
        if time.monotonic() >= expires:
            self._values.pop(key, None)
            return None
        return value

    def put(self, key: str, value: Any) -> None:
        self._values[key] = (time.monotonic() + self.ttl_seconds, value)


@dataclass(slots=True)
class RetryBudget:
    max_retries: int = 2
    used: int = 0

    def consume(self) -> bool:
        if self.used >= self.max_retries:
            return False
        self.used += 1
        return True
