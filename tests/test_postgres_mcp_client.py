import pytest

from app.mcp_servers.postgres_client import (
    ReadOnlyPostgreSQLClient,
)


def test_normalizes_sqlalchemy_asyncpg_url() -> None:
    result = (
        ReadOnlyPostgreSQLClient.normalize_database_url(
            "postgresql+asyncpg://user:pass@postgres:5432/db"
        )
    )

    assert result == (
        "postgresql://user:pass@postgres:5432/db"
    )


def test_rejects_non_postgres_url() -> None:
    with pytest.raises(
        ValueError,
    ):
        ReadOnlyPostgreSQLClient.normalize_database_url(
            "sqlite:///test.db"
        )
