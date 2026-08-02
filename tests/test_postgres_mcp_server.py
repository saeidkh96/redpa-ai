from app.mcp_servers.postgres_server import mcp


def test_postgres_mcp_uses_v2_server_api() -> None:
    assert type(
        mcp,
    ).__name__ == "MCPServer"
