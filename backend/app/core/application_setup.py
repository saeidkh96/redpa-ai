from __future__ import annotations

from fastapi import FastAPI

from app.core.runtime_settings import (
    RuntimeSettings,
)
from app.errors.handlers import (
    register_exception_handlers,
)
from app.logging_config.setup import (
    configure_logging,
)
from app.middleware.correlation import (
    CorrelationMiddleware,
)


def configure_application_runtime(
    application: FastAPI,
) -> None:
    settings = RuntimeSettings.load()

    configure_logging(
        level=settings.log_level,
        json_logs=settings.json_logs,
    )

    application.add_middleware(
        CorrelationMiddleware,
        request_id_header=(
            settings.request_id_header
        ),
        correlation_id_header=(
            settings.correlation_id_header
        ),
    )

    register_exception_handlers(
        application,
        expose_error_details=(
            settings.expose_error_details
        ),
    )
