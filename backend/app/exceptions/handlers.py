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


def build_error_response(
    *,
    code: str,
    message: str,
    request_id: str,
    details: Any | None = None,
) -> dict[str, Any]:
    """Build the standard API error response."""

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
    """Handle expected application exceptions."""

    request_id = get_request_id()

    logger.warning(
        (
            "Application error | code=%s status_code=%s "
            "method=%s path=%s"
        ),
        exc.code,
        exc.status_code,
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_response(
            code=exc.code,
            message=exc.message,
            request_id=request_id,
            details=exc.details,
        ),
        headers=exc.headers,
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""

    request_id = get_request_id()

    if isinstance(exc.detail, str):
        message = exc.detail
        details = None
    else:
        message = "The request could not be completed."
        details = exc.detail

    logger.warning(
        (
            "HTTP error | status_code=%s method=%s "
            "path=%s detail=%s"
        ),
        exc.status_code,
        request.method,
        request.url.path,
        exc.detail,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_response(
            code=f"http_{exc.status_code}",
            message=message,
            request_id=request_id,
            details=details,
        ),
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle request validation errors."""

    request_id = get_request_id()

    validation_errors = [
        {
            "field": ".".join(str(part) for part in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]

    logger.warning(
        "Validation error | method=%s path=%s errors=%s",
        request.method,
        request.url.path,
        validation_errors,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=build_error_response(
            code="validation_error",
            message="The submitted data is invalid.",
            request_id=request_id,
            details=validation_errors,
        ),
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unexpected application errors."""

    request_id = get_request_id()

    logger.exception(
        "Unhandled exception | method=%s path=%s",
        request.method,
        request.url.path,
        exc_info=exc,
    )

    details: Any | None = None

    if settings.debug:
        details = {
            "exception": type(exc).__name__,
            "message": str(exc),
        }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=build_error_response(
            code="internal_server_error",
            message="An unexpected error occurred.",
            request_id=request_id,
            details=details,
        ),
    )


def register_exception_handlers(application: FastAPI) -> None:
    """Register all application exception handlers."""

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