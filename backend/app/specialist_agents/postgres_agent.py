from __future__ import annotations

import os
import re
from typing import Any

import asyncpg

from app.specialist_agents.runtime import (
    build_specialist_agent_card,
    create_specialist_application,
    run_specialist,
)


FORBIDDEN_SQL = re.compile(
    r"\b("
    r"insert|update|delete|merge|copy|alter|create|drop|truncate|"
    r"grant|revoke|vacuum|analyze|cluster|reindex|refresh|"
    r"call|do|execute|prepare|deallocate|listen|notify|"
    r"lock|comment|security|set|reset"
    r")\b",
    flags=re.IGNORECASE,
)


def _normalize_database_url(
    value: str,
) -> str:
    normalized = str(value or "").strip()

    normalized = normalized.replace(
        "postgresql+asyncpg://",
        "postgresql://",
        1,
    )

    if not normalized:
        raise ValueError(
            "DATABASE_URL is required."
        )

    if not normalized.startswith(
        (
            "postgresql://",
            "postgres://",
        )
    ):
        raise ValueError(
            "Only PostgreSQL URLs are supported."
        )

    return normalized


def _extract_sql(
    request: str,
) -> str:
    text = str(request or "").strip()

    if FORBIDDEN_SQL.search(text):
        raise ValueError(
            "Only read-only SQL is allowed."
        )

    match = re.search(
        r"\b((?:select|with|values)\b.+)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if match is None:
        return (
            "SELECT table_schema, table_name "
            "FROM information_schema.tables "
            "WHERE table_schema NOT IN "
            "('pg_catalog', 'information_schema') "
            "ORDER BY table_schema, table_name "
            "LIMIT 100"
        )

    sql = match.group(1).strip().rstrip(";").strip()

    if ";" in sql:
        raise ValueError(
            "Multiple SQL statements are not allowed."
        )

    if (
        "--" in sql
        or "/*" in sql
        or "*/" in sql
    ):
        raise ValueError(
            "SQL comments are not allowed."
        )

    if FORBIDDEN_SQL.search(sql):
        raise ValueError(
            "Only read-only SQL is allowed."
        )

    if not re.match(
        r"^(select|with|values)\b",
        sql,
        flags=re.IGNORECASE,
    ):
        raise ValueError(
            "SQL must begin with SELECT, WITH, or VALUES."
        )

    return sql


async def handle_postgres_request(
    request: str,
) -> dict[str, Any]:
    database_url = _normalize_database_url(
        os.getenv(
            "DATABASE_URL",
            "",
        )
    )

    sql = _extract_sql(request)

    connection = await asyncpg.connect(
        database_url,
        timeout=15.0,
    )

    try:
        async with connection.transaction(
            readonly=True,
        ):
            await connection.execute(
                "SET LOCAL statement_timeout = '10s'"
            )

            rows = await connection.fetch(sql)

    finally:
        await connection.close()

    limited_rows = rows[:200]

    return {
        "success": True,
        "sql": sql,
        "rows": [
            dict(row)
            for row in limited_rows
        ],
        "row_count": len(limited_rows),
        "truncated": len(rows) > len(limited_rows),
        "read_only": True,
    }


PUBLIC_URL = os.getenv(
    "POSTGRES_AGENT_PUBLIC_URL",
    "http://postgres-agent:8062",
)

CARD = build_specialist_agent_card(
    name="RedPA PostgreSQL Agent",
    description=(
        "A strictly read-only remote PostgreSQL specialist."
    ),
    public_url=PUBLIC_URL,
    version="0.6.0",
    skill_id="read_only_database",
    skill_name="Read-only PostgreSQL",
    skill_description=(
        "Inspect PostgreSQL schemas, tables, and validated "
        "read-only query results."
    ),
    tags=[
        "postgresql",
        "sql",
        "database",
        "read-only",
        "tables",
    ],
    examples=[
        "Show database tables.",
        "Run SELECT COUNT(*) FROM users.",
    ],
)

app = create_specialist_application(
    service_name="RedPA PostgreSQL Agent",
    version="0.6.0",
    card=CARD,
    handler=handle_postgres_request,
    capabilities=[
        "read_only_database",
        "sql_analysis",
    ],
)


def main() -> None:
    run_specialist(
        module_path=(
            "app.specialist_agents.postgres_agent:app"
        ),
        host_env="POSTGRES_AGENT_HOST",
        port_env="POSTGRES_AGENT_PORT",
        default_port=8062,
    )


if __name__ == "__main__":
    main()
