import logging
import time
from contextvars import ContextVar
from typing import Final
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


REQUEST_ID_HEADER: Final[str] = "X-Request-ID"

request_id_context: ContextVar[str] = ContextVar(
    "request_id",
    default="-",
)

logger = logging.getLogger(__name__)


def get_request_id() -> str:
    """Return the request ID associated with the current request."""

    return request_id_context.get()


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID and log request execution details."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid4())

        token = request_id_context.set(request_id)
        request.state.request_id = request_id

        start_time = time.perf_counter()

        logger.info(
            "Request started | request_id=%s method=%s path=%s",
            request_id,
            request.method,
            request.url.path,
        )

        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "Request failed | request_id=%s method=%s path=%s",
                request_id,
                request.method,
                request.url.path,
            )
            raise
        finally:
            request_id_context.reset(token)

        process_time_ms = (time.perf_counter() - start_time) * 1000

        response.headers[REQUEST_ID_HEADER] = request_id
        response.headers["X-Process-Time-Ms"] = f"{process_time_ms:.2f}"

        logger.info(
            (
                "Request completed | request_id=%s method=%s "
                "path=%s status_code=%s duration_ms=%.2f"
            ),
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            process_time_ms,
        )

        return response