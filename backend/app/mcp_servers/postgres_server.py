from __future__ import annotations

import os
from typing import Any

from mcp.server import MCPServer
from mcp.server.transport_security import (
    TransportSecuritySettings,
)

from app.mcp_servers.postgres_client import (
    ReadOnlyPostgreSQLClient,
)


SERVER_HOST = os.getenv(
    "POSTGRES_MCP_HOST",
    "0.0.0.0",
)

SERVER_PORT = int(
    os.getenv(
        "POSTGRES_MCP_PORT",
        "8030",
    )
)

_client: ReadOnlyPostgreSQLClient | None = None


def get_client() -> ReadOnlyPostgreSQLClient:
    """
    Lazily create the PostgreSQL client.

    This keeps module import safe for unit tests and local tooling where
    DATABASE_URL may not be configured yet. Runtime validation still occurs
    before the first real database operation.
    """

    global _client

    if _client is None:
        _client = ReadOnlyPostgreSQLClient(
            statement_timeout_ms=int(
                os.getenv(
                    "POSTGRES_MCP_STATEMENT_TIMEOUT_MS",
                    "5000",
                )
            ),
            max_rows=int(
                os.getenv(
                    "POSTGRES_MCP_MAX_ROWS",
                    "200",
                )
            ),
        )

    return _client

mcp = MCPServer(
    "RedPA PostgreSQL",
    instructions=(
        "Read-only access to PostgreSQL schemas, tables, metadata, "
        "SELECT queries, and non-analyzing EXPLAIN plans. "
        "Mutation, DDL, administrative operations, file access, "
        "multiple statements, and row locks are prohibited."
    ),
)


TRANSPORT_SECURITY = TransportSecuritySettings(
    allowed_hosts=[
        "postgres-mcp",
        "postgres-mcp:*",
        "redpa-postgres-mcp",
        "redpa-postgres-mcp:*",
        "127.0.0.1",
        "127.0.0.1:*",
        "localhost",
        "localhost:*",
    ],
    allowed_origins=[],
)


@mcp.tool()
async def list_schemas() -> dict[str, Any]:
    """List user-visible PostgreSQL schemas."""

    schemas = await get_client().list_schemas()

    return {
        "schemas": schemas,
        "count": len(
            schemas,
        ),
        "read_only": True,
    }


@mcp.tool()
async def list_tables(
    schema: str = "public",
) -> dict[str, Any]:
    """
    List tables and views inside a PostgreSQL schema.

    Args:
        schema: PostgreSQL schema name. Defaults to public.
    """

    tables = await get_client().list_tables(
        schema=schema,
    )

    return {
        "schema": schema,
        "tables": tables,
        "count": len(
            tables,
        ),
        "read_only": True,
    }


@mcp.tool()
async def describe_table(
    table: str,
    schema: str = "public",
) -> dict[str, Any]:
    """
    Describe PostgreSQL table columns, constraints, and indexes.

    Args:
        table: Table name.
        schema: PostgreSQL schema name. Defaults to public.
    """

    result = await get_client().describe_table(
        schema=schema,
        table=table,
    )

    return {
        **result,
        "read_only": True,
    }


@mcp.tool()
async def query(
    sql: str,
    max_rows: int = 100,
) -> dict[str, Any]:
    """
    Execute one strictly read-only SELECT, WITH, or VALUES query.

    Args:
        sql: One read-only SQL statement.
        max_rows: Maximum rows returned, capped by server policy.
    """

    return await get_client().query(
        sql,
        max_rows=max_rows,
    )


@mcp.tool()
async def explain(
    sql: str,
) -> dict[str, Any]:
    """
    Return a PostgreSQL JSON execution plan without running ANALYZE.

    Args:
        sql: One read-only SELECT, WITH, or VALUES query.
    """

    return await get_client().explain(
        sql,
    )


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host=SERVER_HOST,
        port=SERVER_PORT,
        streamable_http_path="/mcp",
        stateless_http=True,
        json_response=True,
        transport_security=TRANSPORT_SECURITY,
    )
