from __future__ import annotations

import os
from datetime import (
    datetime,
    timezone,
)

from app.core.config import settings
from app.health.checks import (
    DependencyHealthChecks,
)
from app.health.schemas import (
    HealthResponse,
)


class HealthService:
    @classmethod
    async def liveness(
        cls,
    ) -> HealthResponse:
        return HealthResponse(
            status="healthy",
            service=settings.app_name,
            version=settings.app_version,
            environment=os.getenv(
                "ENVIRONMENT",
                "development",
            ),
            timestamp=datetime.now(
                timezone.utc,
            ),
            dependencies=[],
        )

    @classmethod
    async def readiness(
        cls,
    ) -> HealthResponse:
        dependencies = await (
            DependencyHealthChecks.all_checks()
        )

        critical = {
            "postgres",
            "redis",
            "qdrant",
        }

        ready = all(
            dependency.status == "healthy"
            for dependency in dependencies
            if dependency.name in critical
        )

        return HealthResponse(
            status=(
                "ready"
                if ready
                else "not_ready"
            ),
            service=settings.app_name,
            version=settings.app_version,
            environment=os.getenv(
                "ENVIRONMENT",
                "development",
            ),
            timestamp=datetime.now(
                timezone.utc,
            ),
            dependencies=dependencies,
        )

    @classmethod
    async def deep_health(
        cls,
    ) -> HealthResponse:
        dependencies = await (
            DependencyHealthChecks.all_checks()
        )

        healthy = all(
            dependency.status == "healthy"
            for dependency in dependencies
        )

        return HealthResponse(
            status=(
                "healthy"
                if healthy
                else "degraded"
            ),
            service=settings.app_name,
            version=settings.app_version,
            environment=os.getenv(
                "ENVIRONMENT",
                "development",
            ),
            timestamp=datetime.now(
                timezone.utc,
            ),
            dependencies=dependencies,
        )
