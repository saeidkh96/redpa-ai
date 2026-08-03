from __future__ import annotations

import logging
import time
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import (
    BaseHTTPMiddleware,
)

from app.logging_config.context import (
    bind_request_context,
    reset_request_context,
)


logger = logging.getLogger(
    "redpa.http",
)


class CorrelationMiddleware(
    BaseHTTPMiddleware,
):
    def __init__(
        self,
        app,
        *,
        request_id_header: str = "X-Request-ID",
        correlation_id_header: str = "X-Correlation-ID",
    ) -> None:
        super().__init__(
            app,
        )

        self.request_id_header = (
            request_id_header
        )

        self.correlation_id_header = (
            correlation_id_header
        )

    async def dispatch(
        self,
        request: Request,
        call_next,
    ):
        request_id = (
            request.headers.get(
                self.request_id_header,
            )
            or str(
                uuid4(),
            )
        )

        correlation_id = (
            request.headers.get(
                self.correlation_id_header,
            )
            or request_id
        )

        tokens = bind_request_context(
            request_id=request_id,
            correlation_id=correlation_id,
        )

        started = time.perf_counter()

        try:
            response = await call_next(
                request,
            )

            process_time_ms = round(
                (
                    time.perf_counter()
                    - started
                )
                * 1000,
                2,
            )

            response.headers[
                self.request_id_header
            ] = request_id

            response.headers[
                self.correlation_id_header
            ] = correlation_id

            response.headers[
                "X-Process-Time-Ms"
            ] = str(
                process_time_ms,
            )

            logger.info(
                "HTTP request completed",
                extra={
                    "http_method": request.method,
                    "http_path": request.url.path,
                    "http_status": response.status_code,
                    "process_time_ms": (
                        process_time_ms
                    ),
                },
            )

            return response

        finally:
            reset_request_context(
                tokens,
            )
