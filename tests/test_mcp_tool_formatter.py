from app.formatters.mcp_tool_formatter import (
    format_mcp_tool_response,
)


def test_formats_file_list() -> None:
    response = format_mcp_tool_response(
        qualified_name=(
            "mcp:redpa-filesystem:list_files"
        ),
        success=True,
        structured_content={
            "path": "backend/app/mcp",
            "entries": [
                {
                    "path": (
                        "backend/app/mcp/client.py"
                    ),
                    "type": "file",
                }
            ],
            "truncated": False,
        },
        content=[],
        error=None,
    )

    assert "client.py" in response
    assert "backend/app/mcp" in response
