from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.database.session import (
    check_database_connection,
    close_database_connection,
)
from app.monitoring.metrics import PrometheusMetricsMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Manage application startup and shutdown resources.
    """

    database_is_available = await check_database_connection()

    if not database_is_available:
        print(
            "WARNING: PostgreSQL connection could not be established. "
            "The application will continue running with degraded health."
        )

    yield

    await close_database_connection()


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[
            "X-Request-ID",
            "X-Process-Time-Ms",
        ],
    )

    application.add_middleware(
        PrometheusMetricsMiddleware,
        excluded_paths={
            "/metrics",
            "/api/v1/metrics",
        },
    )

    application.include_router(
        api_router,
        prefix=settings.api_v1_prefix,
    )

    return application


app = create_application()