from __future__ import annotations

from prometheus_client import Counter, Histogram


A2A_MULTI_REQUESTS_TOTAL = Counter(
    "redpa_a2a_multi_requests_total",
    "Total number of RedPA multi-agent workflow requests.",
    labelnames=(
        "status",
    ),
)

A2A_MULTI_SUBTASKS_TOTAL = Counter(
    "redpa_a2a_multi_subtasks_total",
    "Total number of RedPA multi-agent subtasks.",
    labelnames=(
        "status",
        "remote_agent",
    ),
)

A2A_MULTI_DURATION_SECONDS = Histogram(
    "redpa_a2a_multi_duration_seconds",
    "Duration of RedPA multi-agent workflows.",
)

A2A_MULTI_SUBTASK_DURATION_SECONDS = Histogram(
    "redpa_a2a_multi_subtask_duration_seconds",
    "Duration of individual RedPA A2A subtasks.",
    labelnames=(
        "remote_agent",
    ),
)

A2A_APPROVAL_REQUIRED_TOTAL = Counter(
    "redpa_a2a_approval_required_total",
    "Number of multi-agent requests stopped for approval.",
    labelnames=(
        "reason",
    ),
)
