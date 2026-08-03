from __future__ import annotations
import hashlib
import json
import os
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.runtime_cache.redis_client import RedisRuntime

class RedisIdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method not in {"POST", "PUT", "PATCH"}:
            return await call_next(request)

        idem = request.headers.get("Idempotency-Key")
        if not idem:
            return await call_next(request)

        body = await request.body()
        fingerprint = hashlib.sha256(
            request.method.encode() + request.url.path.encode() + body
        ).hexdigest()
        key = f"redpa:idempotency:{idem}"
        client = RedisRuntime.client()
        existing = await client.hgetall(key)

        if existing:
            if existing.get("fingerprint") != fingerprint:
                return Response(
                    json.dumps({"detail": "Idempotency key conflict."}),
                    status_code=409,
                    media_type="application/json",
                )
            return Response(
                existing.get("body", ""),
                status_code=int(existing["status_code"]),
                media_type=existing.get("media_type", "application/json"),
                headers={"X-Idempotency-Replayed": "true"},
            )

        response = await call_next(request)
        data = b""
        async for chunk in response.body_iterator:
            data += chunk

        rebuilt = Response(
            data,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )

        await client.hset(key, mapping={
            "fingerprint": fingerprint,
            "status_code": str(rebuilt.status_code),
            "body": data.decode("utf-8", errors="replace"),
            "media_type": rebuilt.media_type or "application/json",
        })
        await client.expire(
            key,
            int(os.getenv("IDEMPOTENCY_TTL_SECONDS", "86400")),
        )
        rebuilt.headers["X-Idempotency-Replayed"] = "false"
        return rebuilt
