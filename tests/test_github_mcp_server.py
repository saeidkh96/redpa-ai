from app.mcp_servers.github_server import mcp


def test_github_mcp_uses_v2_server_api() -> None:
    assert type(
        mcp,
    ).__name__ == "MCPServer"
