import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.exceptions.handlers import register_exception_handlers
from app.middleware.request_context import RequestContextMiddleware


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Handle application startup and shutdown events.
    """

    logger.info(
        "Application starting",
        extra={
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "environment": settings.environment,
        },
    )

    yield

    logger.info(
        "Application shutting down",
        extra={
            "app_name": settings.app_name,
            "environment": settings.environment,
        },
    )


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """

    configure_logging()

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Enterprise-grade AI platform for intelligent automation, "
            "multi-agent workflows, and retrieval-augmented generation."
        ),
        debug=False,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    configure_middleware(application)
    register_exception_handlers(application)
    register_routers(application)

    return application


def configure_middleware(application: FastAPI) -> None:
    """
    Register application middleware.

    Middleware execution order is reversed in Starlette.
    The middleware added last executes first.
    """

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allowed_methods,
        allow_headers=settings.cors_allowed_headers,
        expose_headers=settings.cors_exposed_headers,
    )

    application.add_middleware(RequestContextMiddleware)


def register_routers(application: FastAPI) -> None:
    """
    Register API routers.
    """

    application.include_router(
        api_router,
        prefix=settings.api_v1_prefix,
    )


app = create_application()