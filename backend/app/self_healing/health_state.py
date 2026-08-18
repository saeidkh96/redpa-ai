from __future__ import annotations

import asyncio
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import StrEnum


class RuntimeHealthStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    RECOVERING = "recovering"


@dataclass(frozen=True, slots=True)
class AgentRuntimeHealth:
    agent_id: str
    status: RuntimeHealthStatus = RuntimeHealthStatus.HEALTHY
    consecutive_failures: int = 0
    total_failures: int = 0
    last_failure_at: datetime | None = None
    last_recovery_at: datetime | None = None
    last_error: str | None = None
    updated_at: datetime | None = None


class AgentRuntimeHealthStore:
    def __init__(self, *, degraded_threshold: int = 1, unavailable_threshold: int = 3) -> None:
        if degraded_threshold < 1 or unavailable_threshold < degraded_threshold:
            raise ValueError("Invalid health thresholds")
        self.degraded_threshold = degraded_threshold
        self.unavailable_threshold = unavailable_threshold
        self._items = {}
        self._lock = asyncio.Lock()

    async def get(self, agent_id: str) -> AgentRuntimeHealth:
        key = agent_id.casefold().strip()
        async with self._lock:
            return self._items.get(key, AgentRuntimeHealth(agent_id=agent_id, updated_at=datetime.now(timezone.utc)))

    async def record_failure(self, agent_id: str, *, error: str | None = None) -> AgentRuntimeHealth:
        key = agent_id.casefold().strip(); now = datetime.now(timezone.utc)
        async with self._lock:
            current = self._items.get(key, AgentRuntimeHealth(agent_id=agent_id))
            consecutive = current.consecutive_failures + 1
            status = RuntimeHealthStatus.UNAVAILABLE if consecutive >= self.unavailable_threshold else RuntimeHealthStatus.DEGRADED
            updated = replace(current, status=status, consecutive_failures=consecutive, total_failures=current.total_failures + 1, last_failure_at=now, last_error=error, updated_at=now)
            self._items[key] = updated
            return updated

    async def record_recovery(self, agent_id: str) -> AgentRuntimeHealth:
        key = agent_id.casefold().strip(); now = datetime.now(timezone.utc)
        async with self._lock:
            current = self._items.get(key, AgentRuntimeHealth(agent_id=agent_id))
            updated = replace(current, status=RuntimeHealthStatus.HEALTHY, consecutive_failures=0, last_recovery_at=now, last_error=None, updated_at=now)
            self._items[key] = updated
            return updated


agent_runtime_health_store = AgentRuntimeHealthStore()
