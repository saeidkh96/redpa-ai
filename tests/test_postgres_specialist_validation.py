import pytest

from app.specialist_agents.postgres_agent import (
    _extract_sql,
)


def test_accepts_select() -> None:
    assert _extract_sql(
        "Run SELECT COUNT(*) FROM users"
    ) == "SELECT COUNT(*) FROM users"


@pytest.mark.parametrize(
    "sql_request",
    [
        "Run DELETE FROM users",
        "Run SELECT * FROM users; DROP TABLE users",
        "Run SELECT * FROM users -- comment",
    ],
)
def test_rejects_unsafe_sql(
    sql_request: str,
) -> None:
    with pytest.raises(
        ValueError,
    ):
        _extract_sql(
            sql_request,
        )
