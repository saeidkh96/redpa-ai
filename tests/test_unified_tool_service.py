from app.services.unified_tool_service import (
    UnifiedToolService,
)


def test_internal_qualified_name() -> None:
    assert (
        UnifiedToolService.internal_qualified_name(
            "Calculator",
        )
        == "internal:calculator"
    )


def test_mcp_qualified_name() -> None:
    assert (
        UnifiedToolService.mcp_qualified_name(
            server_name="Remote Server",
            tool_name="Web Search",
        )
        == "mcp:remote_server:web_search"
    )
