from app.mcp.planner_intent import detect_mcp_tool_intent


def test_list_schemas_intent() -> None:
    intent = detect_mcp_tool_intent(
        "List database schemas"
    )

    assert intent is not None
    assert intent.qualified_name == (
        "mcp:redpa-postgres:list_schemas"
    )


def test_list_tables_intent() -> None:
    intent = detect_mcp_tool_intent(
        "Show database tables"
    )

    assert intent is not None
    assert intent.qualified_name == (
        "mcp:redpa-postgres:list_tables"
    )
    assert intent.arguments["schema"] == "public"


def test_describe_table_intent() -> None:
    intent = detect_mcp_tool_intent(
        "Describe table users"
    )

    assert intent is not None
    assert intent.qualified_name == (
        "mcp:redpa-postgres:describe_table"
    )
    assert intent.arguments == {
        "table": "users",
        "schema": "public",
    }


def test_query_intent() -> None:
    intent = detect_mcp_tool_intent(
        "Run query SELECT COUNT(*) AS user_count FROM users"
    )

    assert intent is not None
    assert intent.qualified_name == (
        "mcp:redpa-postgres:query"
    )
    assert intent.arguments["sql"].startswith(
        "SELECT COUNT(*)"
    )


def test_explain_intent() -> None:
    intent = detect_mcp_tool_intent(
        "Explain SELECT * FROM messages"
    )

    assert intent is not None
    assert intent.qualified_name == (
        "mcp:redpa-postgres:explain"
    )
