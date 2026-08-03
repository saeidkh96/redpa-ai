from __future__ import annotations
import json
import os
from typing import Any
from redis.asyncio import Redis

class RedisRuntime:
    _client: Redis | None = None

    @classmethod
    def client(cls) -> Redis:
        if cls._client is None:
            cls._client = Redis.from_url(
                os.getenv("REDIS_URL", "redis://redis:6379/0"),
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
        return cls._client

    @classmethod
    async def get_json(cls, key: str) -> Any | None:
        value = await cls.client().get(key)
        return None if value is None else json.loads(value)

    @classmethod
    async def set_json(cls, key: str, value: Any, ttl_seconds: int = 300) -> None:
        await cls.client().set(
            key,
            json.dumps(value, ensure_ascii=False, default=str),
            ex=ttl_seconds,
        )
