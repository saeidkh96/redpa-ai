from __future__ import annotations

import asyncio
import os
import time
from typing import Awaitable, Callable

import asyncpg
import httpx

from app.health.schemas import (
    DependencyHealth,
)
from app.runtime_cache.redis_client import (
    RedisRuntime,
)


class DependencyHealthChecks:
    @staticmethod
    def _database_url() -> str:
        return os.getenv(
            "DATABASE_URL",
            "",
        ).replace(
            "postgresql+asyncpg://",
            "postgresql://",
            1,
        )

    @classmethod
    async def postgres(cls) -> DependencyHealth:
        async def check() -> None:
            connection = await asyncpg.connect(
                cls._database_url(),
                timeout=5.0,
            )
            try:
                await connection.fetchval(
                    "SELECT 1"
                )
            finally:
                await connection.close()

        return await cls._timed(
            "postgres",
            check,
        )

    @classmethod
    async def redis(cls) -> DependencyHealth:
        async def check() -> None:
            await RedisRuntime.client().ping()

        return await cls._timed(
            "redis",
            check,
        )

    @classmethod
    async def qdrant(cls) -> DependencyHealth:
        base_url = os.getenv(
            "QDRANT_URL",
            "http://qdrant:6333",
        ).rstrip("/")

        async def check() -> None:
            async with httpx.AsyncClient(
                timeout=5.0,
            ) as client:
                response = await client.get(
                    f"{base_url}/readyz"
                )
                response.raise_for_status()

        return await cls._timed(
            "qdrant",
            check,
        )

    @classmethod
    async def tempo(cls) -> DependencyHealth:
        base_url = os.getenv(
            "TEMPO_URL",
            "http://tempo:3200",
        ).rstrip("/")

        async def check() -> None:
            async with httpx.AsyncClient(
                timeout=5.0,
            ) as client:
                response = await client.get(
                    f"{base_url}/ready"
                )
                response.raise_for_status()

        return await cls._timed(
            "tempo",
            check,
        )

    @classmethod
    async def otel_collector(
        cls,
    ) -> DependencyHealth:
        base_url = os.getenv(
            "OTEL_COLLECTOR_HEALTH_URL",
            "http://otel-collector:13133",
        ).rstrip("/")

        async def check() -> None:
            async with httpx.AsyncClient(
                timeout=5.0,
            ) as client:
                response = await client.get(
                    base_url,
                )
                response.raise_for_status()

        return await cls._timed(
            "otel-collector",
            check,
        )

    @classmethod
    async def background_worker(
        cls,
    ) -> DependencyHealth:
        async def check() -> None:
            client = RedisRuntime.client()
            heartbeat = await client.get(
                "redpa:background-worker:heartbeat"
            )

            if not heartbeat:
                raise RuntimeError(
                    "Background worker heartbeat is missing."
                )

        return await cls._timed(
            "background-worker",
            check,
        )

    @classmethod
    async def background_scheduler(
        cls,
    ) -> DependencyHealth:
        async def check() -> None:
            client = RedisRuntime.client()
            heartbeat = await client.get(
                "redpa:background-scheduler:heartbeat"
            )

            if not heartbeat:
                raise RuntimeError(
                    "Background scheduler heartbeat is missing."
                )

        return await cls._timed(
            "background-scheduler",
            check,
        )

    @classmethod
    async def all_checks(
        cls,
    ) -> list[DependencyHealth]:
        checks = (
            cls.postgres(),
            cls.redis(),
            cls.qdrant(),
            cls.tempo(),
            cls.otel_collector(),
            cls.background_worker(),
            cls.background_scheduler(),
        )

        return list(
            await asyncio.gather(
                *checks,
            )
        )

    @staticmethod
    async def _timed(
        name: str,
        operation: Callable[
            [],
            Awaitable[None],
        ],
    ) -> DependencyHealth:
        started = time.perf_counter()

        try:
            await operation()

            return DependencyHealth(
                name=name,
                status="healthy",
                latency_ms=round(
                    (
                        time.perf_counter()
                        - started
                    )
                    * 1000,
                    2,
                ),
            )

        except Exception as exception:
            return DependencyHealth(
                name=name,
                status="unhealthy",
                latency_ms=round(
                    (
                        time.perf_counter()
                        - started
                    )
                    * 1000,
                    2,
                ),
                detail=str(
                    exception,
                ),
            )
