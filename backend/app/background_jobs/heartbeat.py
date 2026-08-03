from __future__ import annotations

import time

from app.runtime_cache.redis_client import (
    RedisRuntime,
)


class BackgroundHeartbeat:
    @staticmethod
    async def worker() -> None:
        await RedisRuntime.client().set(
            "redpa:background-worker:heartbeat",
            str(
                time.time(),
            ),
            ex=30,
        )

    @staticmethod
    async def scheduler() -> None:
        await RedisRuntime.client().set(
            "redpa:background-scheduler:heartbeat",
            str(
                time.time(),
            ),
            ex=90,
        )
