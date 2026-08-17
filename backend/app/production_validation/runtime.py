from __future__ import annotations

import asyncio
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from app.ops_v9.repository import OpsRepository
from app.ops_v9.schemas import IncidentCreate
from app.production_validation.coordinator import (
    production_recovery_coordinator,
)
from app.production_validation.detector import FailureDetector
from app.production_validation.schemas import HealthProbeResult
from app.production_validation.service import ProductionValidationService


@dataclass(frozen=True, slots=True)
class MonitoredService:
    name: str
    health_url: str


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def monitored_services() -> tuple[MonitoredService, ...]:
    raw = os.getenv(
        "PRODUCTION_VALIDATION_SERVICES",
        "redpa-research-agent=http://research-agent:8061/health",
    ).strip()

    services: list[MonitoredService] = []

    for item in raw.split(","):
        item = item.strip()

        if not item or "=" not in item:
            continue

        name, url = item.split("=", 1)
        name = name.strip()
        url = url.strip()

        if name and url:
            services.append(
                MonitoredService(
                    name=name,
                    health_url=url,
                )
            )

    return tuple(services)


class ProductionValidationRuntime:
    def __init__(self) -> None:
        self.service = ProductionValidationService(
            detector=FailureDetector(
                threshold=_env_int(
                    "PRODUCTION_VALIDATION_FAILURE_THRESHOLD",
                    3,
                ),
                cooldown_seconds=_env_float(
                    "PRODUCTION_VALIDATION_COOLDOWN_SECONDS",
                    300.0,
                ),
            )
        )

        self.timeout_seconds = _env_float(
            "PRODUCTION_VALIDATION_PROBE_TIMEOUT_SECONDS",
            3.0,
        )

    async def probe(
        self,
        target: MonitoredService,
    ) -> HealthProbeResult:
        started = time.perf_counter()

        def _request() -> tuple[bool, str, str | None]:
            try:
                with urllib.request.urlopen(
                    target.health_url,
                    timeout=self.timeout_seconds,
                ) as response:
                    code = int(response.status)

                    return (
                        200 <= code < 300,
                        f"http_{code}",
                        None,
                    )

            except urllib.error.HTTPError as exc:
                return (
                    False,
                    f"http_{exc.code}",
                    str(exc),
                )

            except Exception as exc:
                return (
                    False,
                    "unreachable",
                    str(exc),
                )

        healthy, status, error = await asyncio.to_thread(
            _request
        )

        latency_ms = (
            time.perf_counter() - started
        ) * 1000.0

        return HealthProbeResult(
            service=target.name,
            healthy=healthy,
            status=status,
            latency_ms=latency_ms,
            error=error,
        )

    async def _create_incident(
        self,
        result: HealthProbeResult,
    ):
        existing = await OpsRepository.find_active_incident(
            service=result.service,
            source="production-validation",
        )

        if existing is not None:
            return existing

        return await OpsRepository.create_incident(
            IncidentCreate(
                service=result.service,
                summary=(
                    "Automatic health detection: "
                    f"{result.service} is {result.status}"
                ),
                severity="warning",
                source="production-validation",
                metadata={
                    "automatic": True,
                    "detector": "consecutive-failure",
                    "failure_count": (
                        self.service.detector.failure_count(
                            result.service
                        )
                    ),
                    "probe_status": result.status,
                    "latency_ms": result.latency_ms,
                    "error": result.error,
                },
            )
        )

    async def check_once(self) -> list[object]:
        incidents: list[object] = []

        for target in monitored_services():
            result = await self.probe(target)

            incident = await self.service.evaluate_probe(
                result=result,
                create_incident=self._create_incident,
            )

            if incident is None:
                continue

            incidents.append(incident)

            # Keep logging compatible with both real IncidentRecord
            # objects and lightweight dict mocks used by tests.
            if isinstance(incident, dict):
                incident_id = incident.get("id", "test")
                incident_service = incident.get(
                    "service",
                    result.service,
                )
                incident_status = incident.get(
                    "status",
                    "created",
                )
            else:
                incident_id = getattr(
                    incident,
                    "id",
                    "unknown",
                )
                incident_service = getattr(
                    incident,
                    "service",
                    result.service,
                )
                incident_status = getattr(
                    incident,
                    "status",
                    "created",
                )

            print(
                "[production-validation] "
                f"incident={incident_id} "
                f"service={incident_service} "
                f"status={incident_status}",
                flush=True,
            )

            # Stage 3:
            # Prepare the governed recovery lifecycle.
            #
            # This must never bypass the existing governance /
            # human-approval boundary.
            try:
                run = (
                    await production_recovery_coordinator
                    .prepare_governed_recovery(incident)
                )

                if run is not None:
                    run_id = getattr(
                        run,
                        "id",
                        "unknown",
                    )
                    run_status = getattr(
                        run,
                        "status",
                        "unknown",
                    )

                    print(
                        "[production-validation] "
                        f"governance_run={run_id} "
                        f"status={run_status}",
                        flush=True,
                    )

            except Exception as exc:
                # Governance preparation failure must not terminate
                # the production-validation scheduler.
                print(
                    "[production-validation] "
                    "governance preparation failed: "
                    f"{type(exc).__name__}: {exc}",
                    flush=True,
                )

        return incidents


production_validation_runtime = ProductionValidationRuntime()