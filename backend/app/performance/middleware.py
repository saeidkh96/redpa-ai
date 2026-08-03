from __future__ import annotations

import logging
import os
import time

from fastapi import Request
from starlette.middleware.base import (
    BaseHTTPMiddleware,
)

from app.performance.metrics import (
    REQUEST_DURATION_SECONDS,
    SLOW_REQUESTS_TOTAL,
)


logger = logging.getLogger(
    "redpa.performance",
)


class PerformanceMonitoringMiddleware(
    BaseHTTPMiddleware,
):
    def __init__(
        self,
        app,
        *,
        slow_request_ms: float | None = None,
    ) -> None:
        super().__init__(
            app,
        )

        self.slow_request_ms = (
            slow_request_ms
            or float(
                os.getenv(
                    "SLOW_REQUEST_THRESHOLD_MS",
                    "1000",
                )
            )
        )

    async def dispatch(
        self,
        request: Request,
        call_next,
    ):
        started = time.perf_counter()

        response = await call_next(
            request,
        )

        duration_seconds = (
            time.perf_counter()
            - started
        )

        duration_ms = (
            duration_seconds
            * 1000
        )

        route_path = getattr(
            request.scope.get(
                "route",
            ),
            "path",
            request.url.path,
        )

        REQUEST_DURATION_SECONDS.labels(
            method=request.method,
            path=route_path,
        ).observe(
            duration_seconds,
        )

        response.headers[
            "X-Performance-Time-Ms"
        ] = str(
            round(
                duration_ms,
                2,
            )
        )

        if (
            duration_ms
            >= self.slow_request_ms
        ):
            SLOW_REQUESTS_TOTAL.labels(
                method=request.method,
                path=route_path,
                status=str(
                    response.status_code,
                ),
            ).inc()

            logger.warning(
                "Slow HTTP request detected",
                extra={
                    "http_method": request.method,
                    "http_path": route_path,
                    "http_status": response.status_code,
                    "process_time_ms": round(
                        duration_ms,
                        2,
                    ),
                },
            )

        return response
