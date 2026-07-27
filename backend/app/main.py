import logging

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.exceptions import register_exception_handlers
from app.middleware.request_context import RequestContextMiddleware


configure_logging()

logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""

    application = FastAPI(
        title=f"{settings.app_name} API",
        description=(
            "Backend API for the RedPA AI multi-agent enterprise platform."
        ),
        version=settings.app_version,
        debug=settings.debug,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    register_exception_handlers(application)

    application.add_middleware(
        RequestContextMiddleware,
    )

    application.include_router(
        api_router,
        prefix=settings.api_v1_prefix,
    )

    logger.info(
        "Application configured: name=%s environment=%s version=%s",
        settings.app_name,
        settings.environment,
        settings.app_version,
    )

    return application


app = create_application()