from __future__ import annotations
import hashlib
import json
from typing import Any
from app.runtime_cache.redis_client import RedisRuntime

class DistributedCacheService:
    @staticmethod
    def build_key(namespace: str, payload: Any) -> str:
        raw = json.dumps(payload, sort_keys=True, default=str).encode()
        return f"redpa:cache:{namespace}:{hashlib.sha256(raw).hexdigest()}"

    @classmethod
    async def get_or_set(cls, namespace, payload, producer, ttl_seconds=300):
        key = cls.build_key(namespace, payload)
        cached = await RedisRuntime.get_json(key)
        if cached is not None:
            return cached
        value = await producer()
        await RedisRuntime.set_json(key, value, ttl_seconds)
        return value
