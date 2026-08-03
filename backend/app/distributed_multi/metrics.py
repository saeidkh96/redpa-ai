from prometheus_client import Counter, Histogram


DISTRIBUTED_WORKFLOWS_TOTAL = Counter(
    "redpa_distributed_workflows_total",
    "Total distributed multi-agent workflows.",
    labelnames=("status",),
)

DISTRIBUTED_SUBTASKS_TOTAL = Counter(
    "redpa_distributed_subtasks_total",
    "Total distributed specialist subtasks.",
    labelnames=("status", "remote_agent"),
)

DISTRIBUTED_WORKFLOW_DURATION_SECONDS = Histogram(
    "redpa_distributed_workflow_duration_seconds",
    "Distributed workflow duration.",
)

DISTRIBUTED_SUBTASK_DURATION_SECONDS = Histogram(
    "redpa_distributed_subtask_duration_seconds",
    "Distributed specialist subtask duration.",
    labelnames=("remote_agent",),
)
