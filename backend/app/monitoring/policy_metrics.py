from prometheus_client import Counter, Histogram


POLICY_EVALUATIONS_TOTAL = Counter(
    name="redpa_policy_evaluations_total",
    documentation="Policy evaluations by decision, risk, and source.",
    labelnames=("decision", "risk", "source"),
)

POLICY_ENFORCEMENT_TOTAL = Counter(
    name="redpa_policy_enforcement_total",
    documentation="Policy enforcement outcomes by execution boundary.",
    labelnames=("boundary", "outcome"),
)

POLICY_REVIEW_CREATED_TOTAL = Counter(
    name="redpa_policy_review_created_total",
    documentation="Human reviews created by the policy engine.",
    labelnames=("boundary",),
)

POLICY_EVALUATION_DURATION_SECONDS = Histogram(
    name="redpa_policy_evaluation_duration_seconds",
    documentation="Policy evaluation latency.",
    labelnames=("source",),
)
