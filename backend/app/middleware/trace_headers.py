from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import (
    BaseHTTPMiddleware,
)

from app.observability.context import (
    current_span_id,
    current_trace_id,
)


class TraceHeadersMiddleware(
    BaseHTTPMiddleware,
):
    async def dispatch(
        self,
        request: Request,
        call_next,
    ):
        response = await call_next(
            request,
        )

        trace_id = current_trace_id()
        span_id = current_span_id()

        if trace_id:
            response.headers[
                "X-Trace-ID"
            ] = trace_id

        if span_id:
            response.headers[
                "X-Span-ID"
            ] = span_id

        return response
