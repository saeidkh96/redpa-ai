from prometheus_client import Counter

PRODUCTION_VALIDATION_PROBES_TOTAL = Counter(
    "redpa_production_validation_probes_total",
    "Production validation health probes.",
    ("service", "result"),
)

PRODUCTION_VALIDATION_INCIDENTS_TOTAL = Counter(
    "redpa_production_validation_incidents_total",
    "Incidents created by automatic production validation.",
    ("service",),
)
