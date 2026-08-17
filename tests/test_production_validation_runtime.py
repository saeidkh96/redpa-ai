from __future__ import annotations

import pytest

from app.production_validation.detector import FailureDetector
from app.production_validation.runtime import (
    MonitoredService,
    ProductionValidationRuntime,
)
from app.production_validation.schemas import HealthProbeResult
from app.production_validation.service import ProductionValidationService


@pytest.mark.asyncio
async def test_runtime_reaches_threshold_and_creates_once(monkeypatch) -> None:
    runtime = ProductionValidationRuntime()
    runtime.service = ProductionValidationService(
        detector=FailureDetector(threshold=3, cooldown_seconds=300)
    )

    target = MonitoredService(
        name="redpa-research-agent",
        health_url="http://research-agent:8061/health",
    )

    async def failed_probe(_target):
        return HealthProbeResult(
            service=_target.name,
            healthy=False,
            status="unreachable",
            latency_ms=5.0,
            error="connection refused",
        )

    created = []

    async def create_incident(result):
        created.append(result.service)
        return {"service": result.service}

    runtime.probe = failed_probe
    runtime._create_incident = create_incident

    monkeypatch.setattr(
        "app.production_validation.runtime.monitored_services",
        lambda: (target,),
    )

    assert await runtime.check_once() == []
    assert await runtime.check_once() == []
    third = await runtime.check_once()

    assert third == [{"service": "redpa-research-agent"}]
    assert created == ["redpa-research-agent"]

    # Cooldown prevents another incident signal while the service remains down.
    assert await runtime.check_once() == []
    assert created == ["redpa-research-agent"]


@pytest.mark.asyncio
async def test_healthy_probe_resets_failure_counter(monkeypatch) -> None:
    runtime = ProductionValidationRuntime()
    runtime.service = ProductionValidationService(
        detector=FailureDetector(threshold=2, cooldown_seconds=0)
    )

    target = MonitoredService(
        name="redpa-research-agent",
        health_url="http://research-agent:8061/health",
    )
    states = iter([False, True, False, False])

    async def probe(_target):
        healthy = next(states)
        return HealthProbeResult(
            service=_target.name,
            healthy=healthy,
            status="healthy" if healthy else "unreachable",
        )

    created = []

    async def create_incident(result):
        created.append(result.service)
        return {"service": result.service}

    runtime.probe = probe
    runtime._create_incident = create_incident

    monkeypatch.setattr(
        "app.production_validation.runtime.monitored_services",
        lambda: (target,),
    )

    assert await runtime.check_once() == []
    assert await runtime.check_once() == []
    assert await runtime.check_once() == []
    assert await runtime.check_once() == [{"service": "redpa-research-agent"}]
    assert created == ["redpa-research-agent"]
