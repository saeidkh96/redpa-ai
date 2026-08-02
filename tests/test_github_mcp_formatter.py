from app.formatters.mcp_tool_formatter import (
    format_mcp_tool_response,
)


def test_formats_repository() -> None:
    response = format_mcp_tool_response(
        qualified_name=(
            "mcp:redpa-github:repository"
        ),
        success=True,
        structured_content={
            "repository": "langchain-ai/langgraph",
            "description": "Build resilient agents.",
            "language": "Python",
            "stars": 100,
            "forks": 20,
            "open_issues": 5,
            "default_branch": "main",
            "license": "MIT",
            "archived": False,
            "html_url": (
                "https://github.com/langchain-ai/langgraph"
            ),
        },
        content=[],
        error=None,
    )

    assert "langchain-ai/langgraph" in response
    assert "Stars: 100" in response


def test_formats_commits() -> None:
    response = format_mcp_tool_response(
        qualified_name=(
            "mcp:redpa-github:commits"
        ),
        success=True,
        structured_content={
            "repository": "saeidkh96/redpa-ai",
            "branch": None,
            "commits": [
                {
                    "sha": "abcdef123456",
                    "message": "Add MCP",
                    "author": "Saeid",
                    "date": "2026-08-02T00:00:00Z",
                }
            ],
        },
        content=[],
        error=None,
    )

    assert "Add MCP" in response
    assert "abcdef123456" in response
