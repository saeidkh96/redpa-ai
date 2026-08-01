from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
)


RESEARCH_REQUESTS_TOTAL = Counter(
    name="redpa_research_requests_total",
    documentation=(
        "Total number of RedPA research workflow requests."
    ),
    labelnames=(
        "status",
    ),
)

RESEARCH_DURATION_SECONDS = Histogram(
    name="redpa_research_duration_seconds",
    documentation=(
        "Research workflow duration in seconds."
    ),
    buckets=(
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        30.0,
        60.0,
        120.0,
    ),
)

RESEARCH_EVIDENCE_TOTAL = Counter(
    name="redpa_research_evidence_total",
    documentation=(
        "Total evidence items collected by research workflows."
    ),
    labelnames=(
        "provider",
    ),
)

RESEARCH_DUPLICATES_REMOVED_TOTAL = Counter(
    name="redpa_research_duplicates_removed_total",
    documentation=(
        "Total duplicate research evidence items removed."
    ),
)

RESEARCH_SELECTED_SOURCES = Histogram(
    name="redpa_research_selected_sources",
    documentation=(
        "Number of sources selected for final research responses."
    ),
    buckets=(
        1,
        2,
        3,
        4,
        5,
        6,
        8,
        10,
    ),
)

RESEARCH_CONFIDENCE_SCORE = Gauge(
    name="redpa_research_confidence_score",
    documentation=(
        "Confidence score of the most recent research response."
    ),
)

RESEARCH_RANKING_SCORE = Histogram(
    name="redpa_research_ranking_score",
    documentation=(
        "Average evidence ranking score for research responses."
    ),
    buckets=(
        0.1,
        0.2,
        0.3,
        0.4,
        0.5,
        0.6,
        0.7,
        0.8,
        0.9,
        1.0,
    ),
)
