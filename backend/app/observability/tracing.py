from __future__ import annotations

import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.fastapi import (
    FastAPIInstrumentor,
)
from opentelemetry.instrumentation.httpx import (
    HTTPXClientInstrumentor,
)
from opentelemetry.instrumentation.logging import (
    LoggingInstrumentor,
)
from opentelemetry.instrumentation.redis import (
    RedisInstrumentor,
)
from opentelemetry.instrumentation.asyncpg import (
    AsyncPGInstrumentor,
)
from opentelemetry.sdk.resources import (
    Resource,
    SERVICE_NAME,
    SERVICE_VERSION,
    DEPLOYMENT_ENVIRONMENT,
)
from opentelemetry.sdk.trace import (
    TracerProvider,
)
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
)


_CONFIGURED = False


def configure_tracing(
    app,
    *,
    service_name: str,
    service_version: str,
) -> None:
    global _CONFIGURED

    if _CONFIGURED:
        return

    enabled = os.getenv(
        "OTEL_ENABLED",
        "true",
    ).casefold() in {
        "1",
        "true",
        "yes",
        "on",
    }

    if not enabled:
        return

    resource = Resource.create(
        {
            SERVICE_NAME: service_name,
            SERVICE_VERSION: service_version,
            DEPLOYMENT_ENVIRONMENT: os.getenv(
                "ENVIRONMENT",
                "development",
            ),
        }
    )

    provider = TracerProvider(
        resource=resource,
    )

    endpoint = os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "http://otel-collector:4318",
    ).rstrip("/")

    exporter = OTLPSpanExporter(
        endpoint=f"{endpoint}/v1/traces",
    )

    provider.add_span_processor(
        BatchSpanProcessor(
            exporter,
        )
    )

    trace.set_tracer_provider(
        provider,
    )

    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls=(
            "health,metrics,docs,openapi.json"
        ),
    )

    HTTPXClientInstrumentor().instrument()
    RedisInstrumentor().instrument()
    AsyncPGInstrumentor().instrument()
    LoggingInstrumentor().instrument(
        set_logging_format=True,
    )

    _CONFIGURED = True


def get_tracer(
    name: str = "redpa",
):
    return trace.get_tracer(
        name,
    )
