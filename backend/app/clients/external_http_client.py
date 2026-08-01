from __future__ import annotations

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

from app.clients.http_resilience import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    TTLCache,
    TokenBucketRateLimiter,
)
from app.monitoring.external_http_metrics import (
    EXTERNAL_HTTP_CACHE_TOTAL,
    EXTERNAL_HTTP_CIRCUIT_OPEN_TOTAL,
    EXTERNAL_HTTP_DURATION_SECONDS,
    EXTERNAL_HTTP_REQUESTS_TOTAL,
)
from app.tools.http_exceptions import (
    ExternalToolConnectionError,
    ExternalToolResponseError,
    ExternalToolTimeoutError,
)
from app.tools.http_validators import validate_external_url


@dataclass(slots=True)
class ExternalHTTPResponse:
    status_code: int
    data: Any
    headers: dict[str, str]
    url: str


class ExternalHTTPClient:
    _cache = TTLCache(max_entries=512)
    _limiters: dict[str, TokenBucketRateLimiter] = {}
    _breakers: dict[str, CircuitBreaker] = {}

    def __init__(
        self,
        *,
        timeout_seconds: float = 15.0,
        max_retries: int = 2,
        max_response_bytes: int = 2_000_000,
        user_agent: str = "RedPA-AI/0.2",
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.max_response_bytes = max_response_bytes
        self.user_agent = user_agent

    async def get_json(
        self,
        *,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        allowed_hosts: set[str] | None = None,
        cache_ttl_seconds: float = 0.0,
    ) -> ExternalHTTPResponse:
        validated_url = validate_external_url(
            url,
            allowed_hosts=allowed_hosts,
        )
        host = (urlparse(validated_url).hostname or "unknown").casefold()

        cache_key = self._cache_key(
            validated_url,
            params=params,
            headers=headers,
        )

        if cache_ttl_seconds > 0:
            cached = await self._cache.get(cache_key)
            if cached is not None:
                EXTERNAL_HTTP_CACHE_TOTAL.labels(
                    host=host,
                    result="hit",
                ).inc()
                return cached

            EXTERNAL_HTTP_CACHE_TOTAL.labels(
                host=host,
                result="miss",
            ).inc()

        limiter = self._limiters.setdefault(
            host,
            TokenBucketRateLimiter(
                rate_per_second=5.0,
                capacity=10.0,
            ),
        )
        breaker = self._breakers.setdefault(
            host,
            CircuitBreaker(
                failure_threshold=5,
                recovery_timeout_seconds=30.0,
            ),
        )

        await limiter.acquire()

        try:
            await breaker.before_request()
        except CircuitBreakerOpenError as exception:
            EXTERNAL_HTTP_CIRCUIT_OPEN_TOTAL.labels(host=host).inc()
            raise ExternalToolConnectionError(str(exception)) from exception

        started_at = time.perf_counter()

        try:
            response = await self._request_json(
                url=validated_url,
                params=params,
                headers=headers,
            )
            await breaker.record_success()
            EXTERNAL_HTTP_REQUESTS_TOTAL.labels(
                host=host,
                status="success",
            ).inc()

            if cache_ttl_seconds > 0:
                await self._cache.set(
                    cache_key,
                    response,
                    ttl_seconds=cache_ttl_seconds,
                )

            return response

        except Exception:
            await breaker.record_failure()
            EXTERNAL_HTTP_REQUESTS_TOTAL.labels(
                host=host,
                status="error",
            ).inc()
            raise

        finally:
            EXTERNAL_HTTP_DURATION_SECONDS.labels(
                host=host,
            ).observe(time.perf_counter() - started_at)

    async def _request_json(
        self,
        *,
        url: str,
        params: dict[str, Any] | None,
        headers: dict[str, str] | None,
    ) -> ExternalHTTPResponse:
        request_headers = {
            "Accept": "application/json",
            "User-Agent": self.user_agent,
            **(headers or {}),
        }

        retryable_statuses = {429, 500, 502, 503, 504}

        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(
                        timeout=self.timeout_seconds,
                        connect=min(self.timeout_seconds, 10.0),
                    ),
                    follow_redirects=False,
                ) as client:
                    response = await client.get(
                        url,
                        params=params,
                        headers=request_headers,
                    )

                if (
                    response.status_code in retryable_statuses
                    and attempt < self.max_retries
                ):
                    await asyncio.sleep(0.25 * (2 ** attempt))
                    continue

                if response.is_redirect:
                    raise ExternalToolResponseError(
                        "External redirects are not accepted."
                    )

                response.raise_for_status()

                if len(response.content) > self.max_response_bytes:
                    raise ExternalToolResponseError(
                        "External response exceeded the size limit."
                    )

                try:
                    data = response.json()
                except ValueError as exception:
                    raise ExternalToolResponseError(
                        "External service returned invalid JSON."
                    ) from exception

                return ExternalHTTPResponse(
                    status_code=response.status_code,
                    data=data,
                    headers={
                        key.casefold(): value
                        for key, value in response.headers.items()
                    },
                    url=str(response.url),
                )

            except ExternalToolResponseError:
                raise
            except httpx.TimeoutException as exception:
                if attempt < self.max_retries:
                    await asyncio.sleep(0.25 * (2 ** attempt))
                    continue
                raise ExternalToolTimeoutError(
                    "External service request timed out."
                ) from exception
            except httpx.HTTPStatusError as exception:
                raise ExternalToolResponseError(
                    "External service returned HTTP "
                    f"{exception.response.status_code}: "
                    f"{exception.response.text[:500]}"
                ) from exception
            except httpx.RequestError as exception:
                if attempt < self.max_retries:
                    await asyncio.sleep(0.25 * (2 ** attempt))
                    continue
                raise ExternalToolConnectionError(
                    "Could not communicate with the external service."
                ) from exception

        raise ExternalToolConnectionError(
            "External request failed after all retry attempts."
        )

    @staticmethod
    def _cache_key(
        url: str,
        *,
        params: dict[str, Any] | None,
        headers: dict[str, str] | None,
    ) -> str:
        safe_headers = {
            key.casefold(): value
            for key, value in (headers or {}).items()
            if key.casefold() not in {
                "authorization",
                "x-subscription-token",
                "api-key",
            }
        }

        raw = json.dumps(
            {
                "url": url,
                "params": params or {},
                "headers": safe_headers,
            },
            sort_keys=True,
            default=str,
        ).encode("utf-8")

        return hashlib.sha256(raw).hexdigest()
