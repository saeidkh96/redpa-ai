from __future__ import annotations

import json
import os
from uuid import UUID, uuid4

import asyncpg

from app.connectors_v8.schemas import ConnectorCreate, ConnectorDelivery, ConnectorRecord


class ConnectorNotFoundError(LookupError):
    pass


class ConnectorRepository:
    @staticmethod
    def _database_url() -> str:
        value = os.getenv("DATABASE_URL", "").strip()
        if not value:
            raise RuntimeError("DATABASE_URL is required for connectors.")
        return value.replace("postgresql+asyncpg://", "postgresql://", 1)

    @classmethod
    async def _connect(cls) -> asyncpg.Connection:
        connection = await asyncpg.connect(cls._database_url(), timeout=15.0)
        await connection.set_type_codec("json", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")
        await connection.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")
        return connection

    @classmethod
    async def create(cls, payload: ConnectorCreate) -> ConnectorRecord:
        connector_id = uuid4()
        connection = await cls._connect()
        try:
            row = await connection.fetchrow(
                """
                INSERT INTO enterprise_connectors (
                    id, name, kind, endpoint_url, secret_env_var,
                    enabled, metadata, created_at, updated_at
                ) VALUES ($1,$2,$3,$4,$5,$6,$7::jsonb,NOW(),NOW())
                RETURNING *
                """,
                connector_id,
                payload.name,
                payload.kind,
                str(payload.endpoint_url),
                payload.secret_env_var,
                payload.enabled,
                payload.metadata,
            )
        finally:
            await connection.close()
        return cls._connector(row)

    @classmethod
    async def list(cls, limit: int = 100) -> list[ConnectorRecord]:
        connection = await cls._connect()
        try:
            rows = await connection.fetch(
                "SELECT * FROM enterprise_connectors ORDER BY created_at DESC LIMIT $1",
                limit,
            )
        finally:
            await connection.close()
        return [cls._connector(row) for row in rows]

    @classmethod
    async def get(cls, connector_id: UUID) -> ConnectorRecord:
        connection = await cls._connect()
        try:
            row = await connection.fetchrow("SELECT * FROM enterprise_connectors WHERE id=$1", connector_id)
        finally:
            await connection.close()
        if row is None:
            raise ConnectorNotFoundError(f"Connector was not found: {connector_id}")
        return cls._connector(row)

    @classmethod
    async def create_delivery(cls, connector_id: UUID, *, dry_run: bool) -> UUID:
        delivery_id = uuid4()
        connection = await cls._connect()
        try:
            await connection.execute(
                """
                INSERT INTO connector_deliveries (
                    id, connector_id, status, attempt_count, dry_run, created_at
                ) VALUES ($1,$2,'pending',0,$3,NOW())
                """,
                delivery_id,
                connector_id,
                dry_run,
            )
        finally:
            await connection.close()
        return delivery_id

    @classmethod
    async def finish_delivery(
        cls,
        delivery_id: UUID,
        *,
        status: str,
        attempt_count: int,
        response_status: int | None = None,
        error: str | None = None,
    ) -> ConnectorDelivery:
        connection = await cls._connect()
        try:
            row = await connection.fetchrow(
                """
                UPDATE connector_deliveries
                SET status=$2, attempt_count=$3, response_status=$4,
                    error=$5, completed_at=NOW()
                WHERE id=$1
                RETURNING *
                """,
                delivery_id,
                status,
                attempt_count,
                response_status,
                error,
            )
        finally:
            await connection.close()
        return cls._delivery(row)

    @staticmethod
    def _connector(row) -> ConnectorRecord:
        return ConnectorRecord(
            id=row["id"], name=row["name"], kind=row["kind"], endpoint_url=row["endpoint_url"],
            secret_env_var=row["secret_env_var"], enabled=row["enabled"], metadata=row["metadata"] or {},
            created_at=row["created_at"], updated_at=row["updated_at"],
        )

    @staticmethod
    def _delivery(row) -> ConnectorDelivery:
        return ConnectorDelivery(
            id=row["id"], connector_id=row["connector_id"], status=row["status"],
            attempt_count=row["attempt_count"], response_status=row["response_status"],
            error=row["error"], dry_run=row["dry_run"], created_at=row["created_at"],
            completed_at=row["completed_at"],
        )
