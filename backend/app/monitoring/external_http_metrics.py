from prometheus_client import Counter, Histogram


EXTERNAL_HTTP_REQUESTS_TOTAL = Counter(
    "redpa_external_http_requests_total",
    "External HTTP requests made by RedPA tools.",
    ("host", "status"),
)

EXTERNAL_HTTP_DURATION_SECONDS = Histogram(
    "redpa_external_http_duration_seconds",
    "External HTTP request duration.",
    ("host",),
)

EXTERNAL_HTTP_CACHE_TOTAL = Counter(
    "redpa_external_http_cache_total",
    "External HTTP cache hits and misses.",
    ("host", "result"),
)

EXTERNAL_HTTP_CIRCUIT_OPEN_TOTAL = Counter(
    "redpa_external_http_circuit_open_total",
    "Requests blocked by an open circuit breaker.",
    ("host",),
)
