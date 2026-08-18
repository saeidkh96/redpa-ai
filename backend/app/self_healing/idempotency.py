from __future__ import annotations
import asyncio
from app.self_healing.schemas import FailoverResult

class FailoverIdempotencyStore:
    def __init__(self):
        self._results = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> FailoverResult | None:
        async with self._lock:
            existing = self._results.get(key)
            if existing is None: return None
            return existing.model_copy(update={"duplicate_detected": True, "status": "duplicate" if existing.status == "completed" else existing.status})

    async def put(self, key: str, result: FailoverResult) -> None:
        async with self._lock:
            self._results[key] = result

failover_idempotency_store = FailoverIdempotencyStore()
