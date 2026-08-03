from app.performance.sql_monitor import (
    _operation,
)


def test_extracts_sql_operation() -> None:
    assert _operation(
        "SELECT * FROM users"
    ) == "SELECT"

    assert _operation(
        "  update users set active=true"
    ) == "UPDATE"
