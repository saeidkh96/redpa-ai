from app.mcp.registry import (
    MCPServerRegistry,
)
from app.mcp.schemas import (
    MCPHealthResponse,
    MCPServerConfig,
)


def test_empty_health_response_schema() -> None:
    response = MCPHealthResponse(
        status="healthy",
        configured_servers=0,
        enabled_servers=0,
        connected_servers=0,
        unavailable_servers=0,
        total_tools=0,
        checked_at="2026-08-02T00:00:00Z",
        servers=[],
    )

    assert response.status == "healthy"
    assert response.total_tools == 0


def test_registry_lists_enabled_servers() -> None:
    registry = MCPServerRegistry()

    registry.register(
        MCPServerConfig(
            name="enabled-server",
            url="https://example.com/mcp",
            enabled=True,
        )
    )

    registry.register(
        MCPServerConfig(
            name="disabled-server",
            url="https://example.org/mcp",
            enabled=False,
        )
    )

    enabled = registry.list_enabled()

    assert len(enabled) == 1
    assert enabled[0].name == "enabled-server"
