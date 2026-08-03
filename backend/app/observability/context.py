from __future__ import annotations

from opentelemetry import trace


def current_trace_id() -> str | None:
    span = trace.get_current_span()
    context = span.get_span_context()

    if not context.is_valid:
        return None

    return format(
        context.trace_id,
        "032x",
    )


def current_span_id() -> str | None:
    span = trace.get_current_span()
    context = span.get_span_context()

    if not context.is_valid:
        return None

    return format(
        context.span_id,
        "016x",
    )
