from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send


HTTP_REQUESTS_TOTAL = Counter(
    name="redpa_http_requests_total",
    documentation="Total number of HTTP requests received by RedPA AI.",
    labelnames=(
        "method",
        "path",
        "status_code",
    ),
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    name="redpa_http_request_duration_seconds",
    documentation="HTTP request duration in seconds.",
    labelnames=(
        "method",
        "path",
    ),
    buckets=(
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
    ),
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    name="redpa_http_requests_in_progress",
    documentation="Number of HTTP requests currently being processed.",
    labelnames=(
        "method",
        "path",
    ),
)

HTTP_EXCEPTIONS_TOTAL = Counter(
    name="redpa_http_exceptions_total",
    documentation="Total number of unhandled HTTP request exceptions.",
    labelnames=(
        "method",
        "path",
        "exception_type",
    ),
)

HTTP_RESPONSE_SIZE_BYTES = Histogram(
    name="redpa_http_response_size_bytes",
    documentation="Size of HTTP response bodies in bytes.",
    labelnames=(
        "method",
        "path",
    ),
    buckets=(
        100,
        500,
        1_000,
        5_000,
        10_000,
        50_000,
        100_000,
        500_000,
        1_000_000,
        5_000_000,
    ),
)


def get_request_path(scope: Scope) -> str:
    """
    Return a low-cardinality path label.

    When FastAPI has matched a route, its path template is used, such as:
        /api/v1/reviews/{review_id}

    This avoids generating a separate Prometheus time series for every UUID.
    """

    route = scope.get("route")
    route_path = getattr(route, "path", None)

    if isinstance(route_path, str) and route_path:
        return route_path

    raw_path = scope.get("path")

    if isinstance(raw_path, str) and raw_path:
        return raw_path

    return "unknown"


class PrometheusMetricsMiddleware:
    """
    ASGI middleware that records HTTP request metrics.

    This implementation does not depend on BaseHTTPMiddleware, so streaming
    responses and ASGI behavior remain predictable.
    """

    def __init__(
        self,
        app: ASGIApp,
        excluded_paths: set[str] | None = None,
    ) -> None:
        self.app = app
        self.excluded_paths = excluded_paths or {
            "/metrics",
        }

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        raw_path = request.url.path

        if raw_path in self.excluded_paths:
            await self.app(scope, receive, send)
            return

        method = request.method
        started_at = time.perf_counter()

        status_code = 500
        response_size = 0

        path_before_routing = get_request_path(scope)

        HTTP_REQUESTS_IN_PROGRESS.labels(
            method=method,
            path=path_before_routing,
        ).inc()

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            nonlocal response_size

            if message["type"] == "http.response.start":
                status_code = int(message["status"])

                headers = Headers(
                    raw=message.get("headers", []),
                )

                content_length = headers.get("content-length")

                if content_length is not None:
                    try:
                        response_size = int(content_length)
                    except ValueError:
                        response_size = 0

            elif message["type"] == "http.response.body":
                if response_size == 0:
                    body = message.get("body", b"")
                    response_size += len(body)

            await send(message)

        try:
            await self.app(
                scope,
                receive,
                send_wrapper,
            )

        except Exception as exc:
            final_path = get_request_path(scope)

            HTTP_EXCEPTIONS_TOTAL.labels(
                method=method,
                path=final_path,
                exception_type=type(exc).__name__,
            ).inc()

            raise

        finally:
            duration = time.perf_counter() - started_at
            final_path = get_request_path(scope)

            HTTP_REQUESTS_IN_PROGRESS.labels(
                method=method,
                path=path_before_routing,
            ).dec()

            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                path=final_path,
                status_code=str(status_code),
            ).inc()

            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method,
                path=final_path,
            ).observe(duration)

            HTTP_RESPONSE_SIZE_BYTES.labels(
                method=method,
                path=final_path,
            ).observe(response_size)


async def prometheus_metrics_endpoint() -> Response:
    """
    Return all registered Prometheus metrics.
    """

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
        headers={
            "Cache-Control": "no-store",
        },
    )