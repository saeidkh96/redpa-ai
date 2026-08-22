from __future__ import annotations
import os
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.runtime_cache.redis_client import RedisRuntime

class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in {
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/api/v1/platform/live",
        }:
            return await call_next(request)

        limit = int(os.getenv("RATE_LIMIT_REQUESTS", "120"))
        window = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
        host = request.client.host if request.client else "unknown"
        key = f"redpa:rate:{host}:{int(time.time() // window)}"

        client = RedisRuntime.client()
        current = await client.incr(key)
        if current == 1:
            await client.expire(key, window)

        if current > limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded."},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(limit-current, 0))
        return response
