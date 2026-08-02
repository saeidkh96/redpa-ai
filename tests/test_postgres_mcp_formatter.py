from app.formatters.mcp_tool_formatter import (
    format_mcp_tool_response,
)


def test_formats_tables() -> None:
    response = format_mcp_tool_response(
        qualified_name=(
            "mcp:redpa-postgres:list_tables"
        ),
        success=True,
        structured_content={
            "schema": "public",
            "tables": [
                {
                    "table_name": "users",
                    "table_type": "BASE TABLE",
                }
            ],
        },
        content=[],
        error=None,
    )

    assert "users" in response
    assert "public" in response


def test_formats_query_rows() -> None:
    response = format_mcp_tool_response(
        qualified_name=(
            "mcp:redpa-postgres:query"
        ),
        success=True,
        structured_content={
            "columns": [
                "user_count",
            ],
            "rows": [
                {
                    "user_count": 3,
                }
            ],
            "truncated": False,
        },
        content=[],
        error=None,
    )

    assert "user_count" in response
    assert "3" in response
