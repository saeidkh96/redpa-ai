from __future__ import annotations

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
)


MCP_DISCOVERY_TOTAL = Counter(
    name="redpa_mcp_discovery_total",
    documentation=(
        "Total MCP tool-discovery attempts by server and status."
    ),
    labelnames=(
        "server_name",
        "status",
    ),
)

MCP_DISCOVERY_DURATION_SECONDS = Histogram(
    name="redpa_mcp_discovery_duration_seconds",
    documentation=(
        "Duration of MCP server tool discovery in seconds."
    ),
    labelnames=(
        "server_name",
    ),
    buckets=(
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        30.0,
    ),
)

MCP_DISCOVERED_TOOLS = Gauge(
    name="redpa_mcp_discovered_tools",
    documentation=(
        "Current number of MCP tools discovered per server."
    ),
    labelnames=(
        "server_name",
    ),
)

UNIFIED_TOOL_CATALOG_SIZE = Gauge(
    name="redpa_unified_tool_catalog_size",
    documentation=(
        "Current number of tools in the unified catalog by source."
    ),
    labelnames=(
        "source",
    ),
)
