from app.mcp.naming import (
    build_mcp_qualified_name,
    parse_mcp_qualified_name,
)
from app.mcp.permissions import MCPPermissionService
from app.mcp.schemas import (
    MCPServerConfig,
    MCPToolInfo,
)


def test_qualified_name_round_trip() -> None:
    qualified_name = build_mcp_qualified_name(
        server_name="Example Server",
        tool_name="Web Search",
    )

    assert qualified_name == (
        "mcp:example_server:web_search"
    )

    server_name, tool_name = (
        parse_mcp_qualified_name(
            qualified_name,
        )
    )

    assert server_name == "example_server"
    assert tool_name == "web_search"


def test_permission_requires_approval() -> None:
    server = MCPServerConfig(
        name="example",
        url="https://example.com/mcp",
        requires_approval=True,
    )

    tool = MCPToolInfo(
        server_name="example",
        name="write_file",
        qualified_name="mcp:example:write_file",
        requires_approval=True,
    )

    decision = MCPPermissionService.evaluate(
        server=server,
        tool=tool,
        approval_granted=False,
    )

    assert decision.allowed is False
    assert decision.requires_approval is True


def test_permission_allows_approved_call() -> None:
    server = MCPServerConfig(
        name="example",
        url="https://example.com/mcp",
        requires_approval=True,
    )

    tool = MCPToolInfo(
        server_name="example",
        name="write_file",
        qualified_name="mcp:example:write_file",
        requires_approval=True,
    )

    decision = MCPPermissionService.evaluate(
        server=server,
        tool=tool,
        approval_granted=True,
    )

    assert decision.allowed is True
