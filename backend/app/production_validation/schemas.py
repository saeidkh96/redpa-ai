from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HealthProbeResult:
    service: str
    healthy: bool
    status: str
    latency_ms: float | None = None
    error: str | None = None
