from __future__ import annotations

from typing import Any

from app.errors.codes import (
    ErrorCode,
)


class ApplicationError(
    Exception,
):
    def __init__(
        self,
        *,
        message: str,
        code: ErrorCode,
        status_code: int,
        details: dict[
            str,
            Any,
        ] | None = None,
    ) -> None:
        super().__init__(
            message,
        )

        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class ResourceNotFoundError(
    ApplicationError,
):
    def __init__(
        self,
        message: str,
        *,
        details: dict[
            str,
            Any,
        ] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=ErrorCode.NOT_FOUND,
            status_code=404,
            details=details,
        )


class ResourceConflictError(
    ApplicationError,
):
    def __init__(
        self,
        message: str,
        *,
        details: dict[
            str,
            Any,
        ] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=ErrorCode.CONFLICT,
            status_code=409,
            details=details,
        )


class DependencyUnavailableError(
    ApplicationError,
):
    def __init__(
        self,
        message: str,
        *,
        details: dict[
            str,
            Any,
        ] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=(
                ErrorCode
                .DEPENDENCY_UNAVAILABLE
            ),
            status_code=503,
            details=details,
        )
