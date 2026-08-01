from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
)


MCP_DISCOVERY_TOTAL = Counter(
    name="redpa_mcp_discovery_total",
    documentation="Total MCP discovery attempts.",
    labelnames=(
        "server_name",
        "status",
    ),
)

MCP_DISCOVERY_DURATION_SECONDS = Histogram(
    name="redpa_mcp_discovery_duration_seconds",
    documentation="Duration of MCP discovery.",
    labelnames=(
        "server_name",
    ),
)

MCP_DISCOVERED_TOOLS = Gauge(
    name="redpa_mcp_discovered_tools",
    documentation="MCP tools discovered by server.",
    labelnames=(
        "server_name",
    ),
)

UNIFIED_TOOL_CATALOG_SIZE = Gauge(
    name="redpa_unified_tool_catalog_size",
    documentation="Unified tool-catalog size by source.",
    labelnames=(
        "source",
    ),
)

MCP_HEALTH_CHECKS_TOTAL = Counter(
    name="redpa_mcp_health_checks_total",
    documentation="MCP health checks by server and status.",
    labelnames=(
        "server_name",
        "status",
    ),
)

MCP_HEALTH_CHECK_DURATION_SECONDS = Histogram(
    name="redpa_mcp_health_check_duration_seconds",
    documentation="Duration of MCP health checks.",
    labelnames=(
        "server_name",
    ),
)

MCP_CONNECTED_SERVERS = Gauge(
    name="redpa_mcp_connected_servers",
    documentation="Reachable enabled MCP servers.",
)

MCP_TOOL_CALLS_TOTAL = Counter(
    name="redpa_mcp_tool_calls_total",
    documentation="MCP tool calls by server, tool, and status.",
    labelnames=(
        "server_name",
        "tool_name",
        "status",
    ),
)

MCP_TOOL_CALL_DURATION_SECONDS = Histogram(
    name="redpa_mcp_tool_call_duration_seconds",
    documentation="MCP tool-call duration.",
    labelnames=(
        "server_name",
        "tool_name",
    ),
)

MCP_APPROVAL_BLOCKS_TOTAL = Counter(
    name="redpa_mcp_approval_blocks_total",
    documentation="MCP tool calls blocked pending approval.",
    labelnames=(
        "server_name",
        "tool_name",
    ),
)

MCP_DISCOVERY_CACHE_TOTAL = Counter(
    name="redpa_mcp_discovery_cache_total",
    documentation="MCP discovery cache hits and misses.",
    labelnames=(
        "result",
    ),
)
