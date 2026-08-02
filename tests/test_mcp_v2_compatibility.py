from app.mcp.client import RedPAMCPClient
from app.mcp_servers.filesystem_server import mcp


def test_mcp_server_uses_v2_server_api() -> None:
    assert type(
        mcp,
    ).__name__ == "MCPServer"


def test_v2_http_client_factory() -> None:
    from app.mcp.schemas import MCPServerConfig

    server = MCPServerConfig(
        name="example",
        url="https://example.com/mcp",
        timeout_seconds=15,
    )

    client = RedPAMCPClient._create_http_client(
        server,
    )

    assert client is not None
