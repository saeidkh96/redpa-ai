import pytest

from app.mcp_servers.postgres_security import (
    ReadOnlySQLValidator,
    SQLSecurityError,
)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM users",
        "WITH recent AS (SELECT * FROM messages) SELECT * FROM recent",
        "VALUES (1), (2)",
    ],
)
def test_allows_read_only_queries(
    sql: str,
) -> None:
    validated = ReadOnlySQLValidator.validate_query(
        sql,
    )

    assert validated.statement


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM users",
        "UPDATE users SET email = 'x'",
        "INSERT INTO users(email) VALUES ('x')",
        "DROP TABLE users",
        "SELECT * FROM users; DELETE FROM users",
        "SELECT pg_read_file('/etc/passwd')",
        "SELECT * FROM users FOR UPDATE",
        "SELECT 1 -- comment",
    ],
)
def test_blocks_unsafe_queries(
    sql: str,
) -> None:
    with pytest.raises(
        SQLSecurityError,
    ):
        ReadOnlySQLValidator.validate_query(
            sql,
        )


def test_accepts_safe_explain_query() -> None:
    validated = (
        ReadOnlySQLValidator.validate_explain_query(
            "EXPLAIN SELECT * FROM users"
        )
    )

    assert validated.statement == (
        "SELECT * FROM users"
    )
