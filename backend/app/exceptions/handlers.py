import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status

from app.core.config import settings
from app.exceptions.base import AppException
from app.middleware.request_context import get_request_id


logger = logging.getLogger(__name__)


def resolve_request_id(request: Request) -> str:
    """Return the current request ID from request state or context."""

    return getattr(
        request.state,
        "request_id",
        get_request_id(),
    )


def build_error_response(
    *,
    code: str,
    message: str,
    request_id: str,
    details: Any | None = None,
) -> dict[str, Any]:
    """Create the standard RedPA API error response."""

    error: dict[str, Any] = {
        "code": code,
        "message": message,
        "request_id": request_id,
    }

    if details is not None:
        error["details"] = details

    return {"error": error}


async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    """Handle known application errors."""

    request_id = resolve_request_id(request)

    logger.warning(
        "Application exception | request_id=%s code=%s "
        "status=%s method=%s path=%s",
        request_id,
        exc.code,
        exc.status_code,
        request.method,
        request.url.path,
    )

    response = JSONResponse(
        status_code=exc.status_code,
        content=build_error_response(
            code=exc.code,
            message=exc.message,
            request_id=request_id,
            details=exc.details,
        ),
        headers=exc.headers,
    )

    response.headers["X-Request-ID"] = request_id

    return response


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""

    request_id = resolve_request_id(request)

    if isinstance(exc.detail, str):
        message = exc.detail
        details = None
    else:
        message = "The request could not be completed."
        details = exc.detail

    logger.warning(
        "HTTP exception | request_id=%s status=%s "
        "method=%s path=%s detail=%s",
        request_id,
        exc.status_code,
        request.method,
        request.url.path,
        exc.detail,
    )

    response = JSONResponse(
        status_code=exc.status_code,
        content=build_error_response(
            code=f"http_{exc.status_code}",
            message=message,
            request_id=request_id,
            details=details,
        ),
        headers=exc.headers,
    )

    response.headers["X-Request-ID"] = request_id

    return response


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle invalid request input."""

    request_id = resolve_request_id(request)

    validation_errors = [
        {
            "field": ".".join(
                str(location_part)
                for location_part in error["loc"]
            ),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]

    logger.warning(
        "Validation exception | request_id=%s "
        "method=%s path=%s errors=%s",
        request_id,
        request.method,
        request.url.path,
        validation_errors,
    )

    response = JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=build_error_response(
            code="validation_error",
            message="The submitted data is invalid.",
            request_id=request_id,
            details=validation_errors,
        ),
    )

    response.headers["X-Request-ID"] = request_id

    return response


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unexpected internal errors."""

    request_id = resolve_request_id(request)

    logger.exception(
        "Unhandled exception | request_id=%s method=%s path=%s",
        request_id,
        request.method,
        request.url.path,
        exc_info=exc,
    )

    details: dict[str, str] | None = None

    if settings.debug:
        details = {
            "exception": type(exc).__name__,
            "message": str(exc),
        }

    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=build_error_response(
            code="internal_server_error",
            message="An unexpected error occurred.",
            request_id=request_id,
            details=details,
        ),
    )

    response.headers["X-Request-ID"] = request_id

    return response


def register_exception_handlers(application: FastAPI) -> None:
    """Register all global exception handlers."""

    application.add_exception_handler(
        AppException,
        app_exception_handler,
    )

    application.add_exception_handler(
        HTTPException,
        http_exception_handler,
    )

    application.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )

    application.add_exception_handler(
        Exception,
        unhandled_exception_handler,
    )