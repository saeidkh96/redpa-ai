from __future__ import annotations

import os
import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import asyncpg

from app.mcp_servers.postgres_security import (
    ReadOnlySQLValidator,
)


class PostgreSQLMCPError(RuntimeError):
    """Raised when PostgreSQL MCP cannot complete an operation."""


SYSTEM_SCHEMAS = {
    "information_schema",
    "pg_catalog",
    "pg_toast",
}


class ReadOnlyPostgreSQLClient:
    """Read-only PostgreSQL client with strict time and row limits."""

    def __init__(
        self,
        *,
        database_url: str | None = None,
        statement_timeout_ms: int = 5_000,
        max_rows: int = 200,
    ) -> None:
        self.database_url = self.normalize_database_url(
            database_url
            or os.getenv(
                "DATABASE_URL",
                "",
            )
        )

        self.statement_timeout_ms = max(
            100,
            min(
                int(statement_timeout_ms),
                30_000,
            ),
        )

        self.max_rows = max(
            1,
            min(
                int(max_rows),
                1_000,
            ),
        )

    async def list_schemas(
        self,
    ) -> list[dict[str, Any]]:
        sql = """
            SELECT
                n.nspname AS schema_name,
                pg_get_userbyid(n.nspowner) AS owner_name
            FROM pg_namespace AS n
            WHERE n.nspname NOT LIKE 'pg_temp_%'
              AND n.nspname NOT LIKE 'pg_toast_temp_%'
              AND n.nspname NOT IN (
                  'information_schema',
                  'pg_catalog',
                  'pg_toast'
              )
            ORDER BY n.nspname
        """

        return await self._fetch(
            sql,
        )

    async def list_tables(
        self,
        *,
        schema: str = "public",
    ) -> list[dict[str, Any]]:
        schema_name = ReadOnlySQLValidator.validate_identifier(
            schema,
            field_name="Schema",
        )

        sql = """
            SELECT
                table_schema,
                table_name,
                table_type
            FROM information_schema.tables
            WHERE table_schema = $1
            ORDER BY table_name
        """

        return await self._fetch(
            sql,
            schema_name,
        )

    async def describe_table(
        self,
        *,
        schema: str,
        table: str,
    ) -> dict[str, Any]:
        schema_name = ReadOnlySQLValidator.validate_identifier(
            schema,
            field_name="Schema",
        )

        table_name = ReadOnlySQLValidator.validate_identifier(
            table,
            field_name="Table",
        )

        columns_sql = """
            SELECT
                ordinal_position,
                column_name,
                data_type,
                udt_name,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns
            WHERE table_schema = $1
              AND table_name = $2
            ORDER BY ordinal_position
        """

        constraints_sql = """
            SELECT
                tc.constraint_name,
                tc.constraint_type,
                kcu.column_name
            FROM information_schema.table_constraints AS tc
            LEFT JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
             AND tc.table_name = kcu.table_name
            WHERE tc.table_schema = $1
              AND tc.table_name = $2
            ORDER BY tc.constraint_type, tc.constraint_name, kcu.ordinal_position
        """

        indexes_sql = """
            SELECT
                indexname AS index_name,
                indexdef AS index_definition
            FROM pg_indexes
            WHERE schemaname = $1
              AND tablename = $2
            ORDER BY indexname
        """

        async with self._connection() as connection:
            columns = await connection.fetch(
                columns_sql,
                schema_name,
                table_name,
            )

            if not columns:
                raise PostgreSQLMCPError(
                    f"Table '{schema_name}.{table_name}' was not found."
                )

            constraints = await connection.fetch(
                constraints_sql,
                schema_name,
                table_name,
            )

            indexes = await connection.fetch(
                indexes_sql,
                schema_name,
                table_name,
            )

        return {
            "schema": schema_name,
            "table": table_name,
            "columns": [
                dict(
                    row,
                )
                for row in columns
            ],
            "constraints": [
                dict(
                    row,
                )
                for row in constraints
            ],
            "indexes": [
                dict(
                    row,
                )
                for row in indexes
            ],
        }

    async def query(
        self,
        sql: str,
        *,
        max_rows: int | None = None,
    ) -> dict[str, Any]:
        validated = ReadOnlySQLValidator.validate_query(
            sql,
        )

        requested_limit = (
            self.max_rows
            if max_rows is None
            else max(
                1,
                min(
                    int(max_rows),
                    self.max_rows,
                ),
            )
        )

        wrapped_sql = (
            "SELECT * FROM ("
            + validated.statement
            + ") AS redpa_read_only_query "
            + f"LIMIT {requested_limit + 1}"
        )

        rows = await self._fetch(
            wrapped_sql,
        )

        truncated = len(
            rows,
        ) > requested_limit

        selected_rows = rows[
            :requested_limit
        ]

        columns = (
            list(
                selected_rows[0].keys(),
            )
            if selected_rows
            else []
        )

        return {
            "columns": columns,
            "rows": selected_rows,
            "row_count": len(
                selected_rows,
            ),
            "truncated": truncated,
            "max_rows": requested_limit,
            "read_only": True,
        }

    async def explain(
        self,
        sql: str,
    ) -> dict[str, Any]:
        validated = (
            ReadOnlySQLValidator.validate_explain_query(
                sql,
            )
        )

        explain_sql = (
            "EXPLAIN "
            "(FORMAT JSON, ANALYZE FALSE, VERBOSE FALSE, "
            "COSTS TRUE, BUFFERS FALSE) "
            + validated.statement
        )

        rows = await self._fetch(
            explain_sql,
        )

        plan = (
            rows[0].get(
                "QUERY PLAN",
            )
            if rows
            else None
        )

        return {
            "query": validated.statement,
            "plan": plan,
            "analyze": False,
            "read_only": True,
        }

    async def _fetch(
        self,
        sql: str,
        *arguments: Any,
    ) -> list[dict[str, Any]]:
        try:
            async with self._connection() as connection:
                rows = await connection.fetch(
                    sql,
                    *arguments,
                )

        except asyncpg.PostgresError as exception:
            raise PostgreSQLMCPError(
                f"PostgreSQL rejected the read-only request: "
                f"{exception}"
            ) from exception

        except OSError as exception:
            raise PostgreSQLMCPError(
                "Could not connect to PostgreSQL."
            ) from exception

        return [
            self._serialize_row(
                row,
            )
            for row in rows
        ]

    def _connection(
        self,
    ) -> "_ReadOnlyConnectionContext":
        return _ReadOnlyConnectionContext(
            database_url=self.database_url,
            statement_timeout_ms=(
                self.statement_timeout_ms
            ),
        )

    @staticmethod
    def normalize_database_url(
        value: str,
    ) -> str:
        normalized = str(
            value
            or "",
        ).strip()

        if not normalized:
            raise ValueError(
                "DATABASE_URL is required for PostgreSQL MCP."
            )

        normalized = normalized.replace(
            "postgresql+asyncpg://",
            "postgresql://",
            1,
        )

        parts = urlsplit(
            normalized,
        )

        if parts.scheme not in {
            "postgres",
            "postgresql",
        }:
            raise ValueError(
                "PostgreSQL MCP requires a PostgreSQL DATABASE_URL."
            )

        if not parts.hostname:
            raise ValueError(
                "DATABASE_URL must contain a database hostname."
            )

        return urlunsplit(
            parts,
        )

    @staticmethod
    def _serialize_row(
        row: asyncpg.Record,
    ) -> dict[str, Any]:
        serialized: dict[str, Any] = {}

        for key, value in dict(
            row,
        ).items():
            if value is None or isinstance(
                value,
                (
                    bool,
                    float,
                    int,
                    str,
                    list,
                    dict,
                ),
            ):
                serialized[
                    key
                ] = value
                continue

            isoformat = getattr(
                value,
                "isoformat",
                None,
            )

            if callable(
                isoformat,
            ):
                serialized[
                    key
                ] = isoformat()
            else:
                serialized[
                    key
                ] = str(
                    value,
                )

        return serialized


class _ReadOnlyConnectionContext:
    def __init__(
        self,
        *,
        database_url: str,
        statement_timeout_ms: int,
    ) -> None:
        self.database_url = database_url
        self.statement_timeout_ms = statement_timeout_ms
        self.connection: asyncpg.Connection | None = None
        self.transaction: asyncpg.Transaction | None = None

    async def __aenter__(
        self,
    ) -> asyncpg.Connection:
        self.connection = await asyncpg.connect(
            self.database_url,
            timeout=10.0,
        )

        self.transaction = self.connection.transaction(
            readonly=True,
        )

        await self.transaction.start()

        await self.connection.execute(
            "SET LOCAL statement_timeout = "
            + str(
                self.statement_timeout_ms,
            )
        )

        await self.connection.execute(
            "SET LOCAL lock_timeout = '1000ms'"
        )

        await self.connection.execute(
            "SET LOCAL idle_in_transaction_session_timeout = '10000ms'"
        )

        return self.connection

    async def __aexit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:
        try:
            if self.transaction is not None:
                await self.transaction.rollback()
        finally:
            if self.connection is not None:
                await self.connection.close()
