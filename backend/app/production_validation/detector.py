from __future__ import annotations

import time
from collections import defaultdict
from typing import Awaitable, Callable

from app.production_validation.schemas import HealthProbeResult

Probe = Callable[[str], Awaitable[HealthProbeResult]]


class FailureDetector:
    """Consecutive-failure detector with per-service cooldown."""

    def __init__(self, *, threshold: int = 3, cooldown_seconds: float = 300.0) -> None:
        if threshold < 1:
            raise ValueError("threshold must be >= 1")
        self.threshold = threshold
        self.cooldown_seconds = cooldown_seconds
        self._failures: dict[str, int] = defaultdict(int)
        self._last_triggered: dict[str, float] = {}

    def observe(self, result: HealthProbeResult) -> bool:
        service = result.service
        if result.healthy:
            self._failures[service] = 0
            return False

        self._failures[service] += 1
        if self._failures[service] < self.threshold:
            return False

        now = time.monotonic()
        last = self._last_triggered.get(service)
        if last is not None and now - last < self.cooldown_seconds:
            return False

        self._last_triggered[service] = now
        return True

    def failure_count(self, service: str) -> int:
        return self._failures.get(service, 0)
