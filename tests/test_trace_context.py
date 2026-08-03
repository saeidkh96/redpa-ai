from app.observability.context import (
    current_span_id,
    current_trace_id,
)


def test_trace_helpers_without_active_span():
    assert current_trace_id() is None
    assert current_span_id() is None
