from prometheus_client import (
    Counter,
    Histogram,
)


SLOW_REQUESTS_TOTAL = Counter(
    "redpa_slow_requests_total",
    "Total number of slow HTTP requests.",
    [
        "method",
        "path",
        "status",
    ],
)

REQUEST_DURATION_SECONDS = Histogram(
    "redpa_request_duration_seconds",
    "HTTP request duration in seconds.",
    [
        "method",
        "path",
    ],
)

SLOW_SQL_QUERIES_TOTAL = Counter(
    "redpa_slow_sql_queries_total",
    "Total number of slow SQL queries.",
    [
        "operation",
    ],
)

SQL_QUERY_DURATION_SECONDS = Histogram(
    "redpa_sql_query_duration_seconds",
    "SQL query duration in seconds.",
    [
        "operation",
    ],
)
