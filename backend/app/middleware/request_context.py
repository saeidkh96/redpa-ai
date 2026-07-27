import logging
import time
from contextvars import ContextVar
from typing import Final
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)


REQUEST_ID_HEADER: Final[str] = "X-Request-ID"
PROCESS_TIME_HEADER: Final[str] = "X-Process-Time-Ms"

request_id_context: ContextVar[str] = ContextVar(
    "request_id",
    default="-",
)

logger = logging.getLogger(__name__)


def get_request_id() -> str:
    """Return the request ID for the current async context."""

    return request_id_context.get()


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Add request ID, timing headers and request logs."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = (
            request.headers.get(REQUEST_ID_HEADER)
            or str(uuid4())
        )

        token = request_id_context.set(request_id)
        request.state.request_id = request_id

        started_at = time.perf_counter()

        logger.info(
            "Request started | request_id=%s method=%s path=%s",
            request_id,
            request.method,
            request.url.path,
        )

        try:
            response = await call_next(request)

            process_time_ms = (
                time.perf_counter() - started_at
            ) * 1000

            response.headers[REQUEST_ID_HEADER] = request_id
            response.headers[PROCESS_TIME_HEADER] = (
                f"{process_time_ms:.2f}"
            )

            logger.info(
                "Request completed | request_id=%s method=%s "
                "path=%s status=%s duration_ms=%.2f",
                request_id,
                request.method,
                request.url.path,
                response.status_code,
                process_time_ms,
            )

            return response

        except Exception:
            process_time_ms = (
                time.perf_counter() - started_at
            ) * 1000

            logger.exception(
                "Request failed | request_id=%s method=%s "
                "path=%s duration_ms=%.2f",
                request_id,
                request.method,
                request.url.path,
                process_time_ms,
            )

            raise

        finally:
            request_id_context.reset(token)