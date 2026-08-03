from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
)
from fastapi.exceptions import (
    RequestValidationError,
)
from fastapi.responses import (
    JSONResponse,
)

from app.errors.codes import (
    ErrorCode,
)
from app.errors.exceptions import (
    ApplicationError,
)
from app.logging_config.context import (
    correlation_id_context,
    request_id_context,
)


logger = logging.getLogger(
    "redpa.errors",
)


def _payload(
    *,
    request: Request,
    error_id: str,
    code: str,
    message: str,
    details: dict,
) -> dict:
    return {
        "error": {
            "error_id": error_id,
            "code": code,
            "message": message,
            "details": details,
            "request_id": (
                request_id_context.get()
            ),
            "correlation_id": (
                correlation_id_context.get()
            ),
            "path": request.url.path,
            "method": request.method,
        }
    }


def register_exception_handlers(
    application: FastAPI,
    *,
    expose_error_details: bool = False,
) -> None:
    @application.exception_handler(
        ApplicationError,
    )
    async def handle_application_error(
        request: Request,
        exception: ApplicationError,
    ) -> JSONResponse:
        error_id = str(
            uuid4(),
        )

        logger.warning(
            exception.message,
            extra={
                "error_id": error_id,
                "error_code": (
                    exception.code.value
                ),
                "http_method": request.method,
                "http_path": request.url.path,
                "http_status": (
                    exception.status_code
                ),
            },
        )

        return JSONResponse(
            status_code=(
                exception.status_code
            ),
            content=_payload(
                request=request,
                error_id=error_id,
                code=exception.code.value,
                message=exception.message,
                details=exception.details,
            ),
        )

    @application.exception_handler(
        RequestValidationError,
    )
    async def handle_validation_error(
        request: Request,
        exception: RequestValidationError,
    ) -> JSONResponse:
        error_id = str(
            uuid4(),
        )

        details = {
            "validation_errors": (
                exception.errors()
            ),
        }

        logger.warning(
            "Request validation failed",
            extra={
                "error_id": error_id,
                "error_code": (
                    ErrorCode
                    .VALIDATION_ERROR
                    .value
                ),
                "http_method": request.method,
                "http_path": request.url.path,
                "http_status": 422,
            },
        )

        return JSONResponse(
            status_code=422,
            content=_payload(
                request=request,
                error_id=error_id,
                code=(
                    ErrorCode
                    .VALIDATION_ERROR
                    .value
                ),
                message=(
                    "The request payload is invalid."
                ),
                details=details,
            ),
        )

    @application.exception_handler(
        HTTPException,
    )
    async def handle_http_exception(
        request: Request,
        exception: HTTPException,
    ) -> JSONResponse:
        error_id = str(
            uuid4(),
        )

        code = (
            ErrorCode.NOT_FOUND.value
            if exception.status_code == 404
            else ErrorCode.CONFLICT.value
            if exception.status_code == 409
            else ErrorCode.AUTHENTICATION_ERROR.value
            if exception.status_code == 401
            else ErrorCode.AUTHORIZATION_ERROR.value
            if exception.status_code == 403
            else ErrorCode.INTERNAL_ERROR.value
        )

        message = (
            str(
                exception.detail,
            )
            if exception.detail
            else "HTTP request failed."
        )

        return JSONResponse(
            status_code=(
                exception.status_code
            ),
            content=_payload(
                request=request,
                error_id=error_id,
                code=code,
                message=message,
                details={},
            ),
            headers=exception.headers,
        )

    @application.exception_handler(
        Exception,
    )
    async def handle_unexpected_error(
        request: Request,
        exception: Exception,
    ) -> JSONResponse:
        error_id = str(
            uuid4(),
        )

        logger.exception(
            "Unhandled application error",
            extra={
                "error_id": error_id,
                "error_code": (
                    ErrorCode
                    .INTERNAL_ERROR
                    .value
                ),
                "http_method": request.method,
                "http_path": request.url.path,
                "http_status": 500,
            },
        )

        details = (
            {
                "exception_type": (
                    type(
                        exception,
                    ).__name__
                ),
                "exception_message": (
                    str(
                        exception,
                    )
                ),
            }
            if expose_error_details
            else {}
        )

        return JSONResponse(
            status_code=500,
            content=_payload(
                request=request,
                error_id=error_id,
                code=(
                    ErrorCode
                    .INTERNAL_ERROR
                    .value
                ),
                message=(
                    "An unexpected internal error occurred."
                ),
                details=details,
            ),
        )
