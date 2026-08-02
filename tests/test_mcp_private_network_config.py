from app.mcp.schemas import MCPServerConfig
from app.mcp.security import validate_remote_mcp_url


def test_trusted_docker_mcp_url_is_allowed() -> None:
    server = MCPServerConfig(
        name="redpa-filesystem",
        url="http://filesystem-mcp:8010/mcp",
        allow_private_network=True,
    )

    assert validate_remote_mcp_url(
        str(
            server.url,
        ),
        allow_private_network=(
            server.allow_private_network
        ),
    ).startswith(
        "http://filesystem-mcp:8010"
    )
