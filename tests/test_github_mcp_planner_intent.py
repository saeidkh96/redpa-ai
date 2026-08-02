from app.mcp.planner_intent import (
    detect_mcp_tool_intent,
)


def test_repository_intent() -> None:
    intent = detect_mcp_tool_intent(
        "Show repository langchain-ai/langgraph"
    )

    assert intent is not None
    assert intent.qualified_name == (
        "mcp:redpa-github:repository"
    )
    assert intent.arguments == {
        "repository": "langchain-ai/langgraph",
    }


def test_commits_intent() -> None:
    intent = detect_mcp_tool_intent(
        "Show latest 5 commits of saeidkh96/redpa-ai"
    )

    assert intent is not None
    assert intent.qualified_name == (
        "mcp:redpa-github:commits"
    )
    assert intent.arguments["repository"] == (
        "saeidkh96/redpa-ai"
    )
    assert intent.arguments["limit"] == 5


def test_open_issues_intent() -> None:
    intent = detect_mcp_tool_intent(
        "List 10 open issues of langchain-ai/langgraph"
    )

    assert intent is not None
    assert intent.qualified_name == (
        "mcp:redpa-github:issues"
    )
    assert intent.arguments["state"] == "open"
    assert intent.arguments["limit"] == 10


def test_pull_requests_intent() -> None:
    intent = detect_mcp_tool_intent(
        "Show closed pull requests for openai/openai-python"
    )

    assert intent is not None
    assert intent.qualified_name == (
        "mcp:redpa-github:pull_requests"
    )
    assert intent.arguments["state"] == "closed"


def test_branches_intent() -> None:
    intent = detect_mcp_tool_intent(
        "List branches of langchain-ai/langgraph"
    )

    assert intent is not None
    assert intent.qualified_name == (
        "mcp:redpa-github:branches"
    )
