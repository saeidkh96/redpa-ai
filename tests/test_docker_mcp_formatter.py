from app.formatters.mcp_tool_formatter import (
    format_mcp_tool_response,
)


def test_formats_container_list() -> None:
    response = format_mcp_tool_response(
        qualified_name=(
            "mcp:redpa-docker:list_containers"
        ),
        success=True,
        structured_content={
            "containers": [
                {
                    "names": [
                        "redpa-backend",
                    ],
                    "image": "redpa-ai-backend",
                    "state": "running",
                    "status": "Up 1 minute",
                    "id": "abc123",
                }
            ],
        },
        content=[],
        error=None,
    )

    assert "redpa-backend" in response
    assert "running" in response


def test_formats_logs() -> None:
    response = format_mcp_tool_response(
        qualified_name=(
            "mcp:redpa-docker:container_logs"
        ),
        success=True,
        structured_content={
            "container": "redpa-backend",
            "logs": [
                "Application startup complete.",
            ],
        },
        content=[],
        error=None,
    )

    assert "Application startup complete" in response
