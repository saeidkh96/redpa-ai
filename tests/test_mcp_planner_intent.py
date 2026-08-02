from app.mcp.planner_intent import (
    detect_mcp_tool_intent,
)


def test_list_files_intent() -> None:
    intent = detect_mcp_tool_intent(
        "Show files inside backend/app/mcp"
    )

    assert intent is not None
    assert intent.qualified_name == (
        "mcp:redpa-filesystem:list_files"
    )
    assert intent.arguments["path"] == (
        "backend/app/mcp"
    )


def test_read_file_intent() -> None:
    intent = detect_mcp_tool_intent(
        "Read backend/app/main.py"
    )

    assert intent is not None
    assert intent.qualified_name == (
        "mcp:redpa-filesystem:read_file"
    )
    assert intent.arguments["path"] == (
        "backend/app/main.py"
    )


def test_search_files_intent() -> None:
    intent = detect_mcp_tool_intent(
        "Search for MCPManager in backend/app"
    )

    assert intent is not None
    assert intent.qualified_name == (
        "mcp:redpa-filesystem:search_files"
    )
    assert intent.arguments["query"] == "MCPManager"
    assert intent.arguments["path"] == "backend/app"


def test_unrelated_request_has_no_mcp_intent() -> None:
    assert detect_mcp_tool_intent(
        "Explain what LangGraph is"
    ) is None
