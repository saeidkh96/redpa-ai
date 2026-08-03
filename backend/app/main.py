from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.application_setup import configure_application_runtime
from app.database.session import (
    check_database_connection,
    close_database_connection,
)
from app.middleware.idempotency import RedisIdempotencyMiddleware
from app.middleware.rate_limit import RedisRateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.trace_headers import TraceHeadersMiddleware
from app.monitoring.metrics import PrometheusMetricsMiddleware
from app.performance import PerformanceMonitoringMiddleware, register_sql_performance_monitor
from app.observability.tracing import configure_tracing
from app.security_hardening.config import SecuritySettings


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

    security_settings = SecuritySettings.load()

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
        SecurityHeadersMiddleware,
        require_https=security_settings.require_https,
    )

    application.add_middleware(
        TraceHeadersMiddleware,
    )

    application.add_middleware(
        RedisRateLimitMiddleware,
    )

    application.add_middleware(
        RedisIdempotencyMiddleware,
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
            "X-Trace-ID",
            "X-Span-ID",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-Idempotency-Replayed",
        ],
    )

    application.add_middleware(
        PerformanceMonitoringMiddleware,
    )

    application.add_middleware(
        PrometheusMetricsMiddleware,
        excluded_paths={
            "/metrics",
            "/api/v1/metrics",
        },
    )


    configure_application_runtime(application)
    application.include_router(
        api_router,
        prefix=settings.api_v1_prefix,
    )


    from app.database.session import engine as database_engine
    register_sql_performance_monitor(database_engine)
    configure_tracing(
        application,
        service_name="redpa-backend",
        service_version=settings.app_version,
    )

    return application


app = create_application()