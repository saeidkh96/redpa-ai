from __future__ import annotations

import json
import os
from uuid import UUID, uuid4

import asyncpg

from app.ops_v9.schemas import IncidentCreate, IncidentRecord, OpsActionRecord


class IncidentNotFoundError(LookupError):
    pass


class OpsRepository:
    @staticmethod
    def _database_url() -> str:
        value = os.getenv("DATABASE_URL", "").strip()
        if not value:
            raise RuntimeError("DATABASE_URL is required for V9 operations.")

        return value.replace(
            "postgresql+asyncpg://",
            "postgresql://",
            1,
        )

    @classmethod
    async def _connect(cls) -> asyncpg.Connection:
        connection = await asyncpg.connect(
            cls._database_url(),
            timeout=15.0,
        )

        await connection.set_type_codec(
            "json",
            encoder=json.dumps,
            decoder=json.loads,
            schema="pg_catalog",
        )

        await connection.set_type_codec(
            "jsonb",
            encoder=json.dumps,
            decoder=json.loads,
            schema="pg_catalog",
        )

        return connection

    @classmethod
    async def create_incident(
        cls,
        payload: IncidentCreate,
    ) -> IncidentRecord:
        connection = await cls._connect()

        try:
            row = await connection.fetchrow(
                """
                INSERT INTO ops_incidents
                    (
                        id,
                        service,
                        summary,
                        severity,
                        status,
                        source,
                        diagnosis,
                        metadata,
                        created_at,
                        updated_at
                    )
                VALUES (
                    $1,
                    $2,
                    $3,
                    $4,
                    'open',
                    $5,
                    '{}'::jsonb,
                    $6::jsonb,
                    NOW(),
                    NOW()
                )
                RETURNING *
                """,
                uuid4(),
                payload.service,
                payload.summary,
                payload.severity,
                payload.source,
                payload.metadata,
            )
        finally:
            await connection.close()

        return cls._incident(row)

    @classmethod
    async def list_incidents(
        cls,
        limit: int = 100,
    ) -> list[IncidentRecord]:
        connection = await cls._connect()

        try:
            rows = await connection.fetch(
                """
                SELECT *
                FROM ops_incidents
                ORDER BY created_at DESC
                LIMIT $1
                """,
                limit,
            )
        finally:
            await connection.close()

        return [cls._incident(row) for row in rows]

    @classmethod
    async def find_active_incident(
        cls,
        *,
        service: str,
        source: str,
    ) -> IncidentRecord | None:
        connection = await cls._connect()

        try:
            row = await connection.fetchrow(
                """
                SELECT *
                FROM ops_incidents
                WHERE service = $1
                  AND source = $2
                  AND status IN (
                      'open',
                      'diagnosed',
                      'mitigating'
                  )
                ORDER BY created_at DESC
                LIMIT 1
                """,
                service,
                source,
            )
        finally:
            await connection.close()

        if row is None:
            return None

        return cls._incident(row)

    @classmethod
    async def get_incident(
        cls,
        incident_id: UUID,
    ) -> IncidentRecord:
        connection = await cls._connect()

        try:
            row = await connection.fetchrow(
                """
                SELECT *
                FROM ops_incidents
                WHERE id = $1
                """,
                incident_id,
            )
        finally:
            await connection.close()

        if row is None:
            raise IncidentNotFoundError(
                f"Incident was not found: {incident_id}"
            )

        return cls._incident(row)

    @classmethod
    async def set_diagnosis(
        cls,
        incident_id: UUID,
        diagnosis: dict,
    ) -> IncidentRecord:
        connection = await cls._connect()

        try:
            row = await connection.fetchrow(
                """
                UPDATE ops_incidents
                SET
                    diagnosis = $2::jsonb,
                    status = 'diagnosed',
                    updated_at = NOW()
                WHERE id = $1
                RETURNING *
                """,
                incident_id,
                diagnosis,
            )
        finally:
            await connection.close()

        if row is None:
            raise IncidentNotFoundError(
                f"Incident was not found: {incident_id}"
            )

        return cls._incident(row)

    @classmethod
    async def set_incident_status(
        cls,
        incident_id: UUID,
        status: str,
    ) -> IncidentRecord:
        connection = await cls._connect()

        try:
            row = await connection.fetchrow(
                """
                UPDATE ops_incidents
                SET
                    status = $2::varchar,
                    updated_at = NOW(),
                    resolved_at = CASE
                        WHEN $2::varchar = 'resolved'::varchar
                        THEN NOW()
                        ELSE resolved_at
                    END
                WHERE id = $1
                RETURNING *
                """,
                incident_id,
                status,
            )
        finally:
            await connection.close()

        if row is None:
            raise IncidentNotFoundError(
                f"Incident was not found: {incident_id}"
            )

        return cls._incident(row)

    @classmethod
    async def create_action(
        cls,
        incident_id: UUID,
        *,
        action: str,
        target: str,
        approved: bool,
        reason: str,
        idempotency_key: str | None = None,
    ) -> OpsActionRecord:
        connection = await cls._connect()

        try:
            row = await connection.fetchrow(
                """
                WITH inserted AS (
                    INSERT INTO ops_actions
                        (id, incident_id, action, target, status, approved, reason,
                         result, idempotency_key, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, '{}'::jsonb, $8, NOW())
                    ON CONFLICT (incident_id, idempotency_key) DO NOTHING
                    RETURNING *, FALSE AS duplicate_detected
                )
                SELECT * FROM inserted
                UNION ALL
                SELECT a.*, TRUE AS duplicate_detected
                FROM ops_actions AS a
                WHERE a.incident_id = $2
                  AND a.idempotency_key = $8
                  AND NOT EXISTS (SELECT 1 FROM inserted)
                LIMIT 1
                """,
                uuid4(), incident_id, action, target,
                "approved" if approved else "planned", approved, reason, idempotency_key,
            )
        finally:
            await connection.close()

        return cls._action(row)

    @classmethod
    async def finish_action(
        cls,
        action_id: UUID,
        *,
        status: str,
        result: dict | None = None,
        error: str | None = None,
    ) -> OpsActionRecord:
        connection = await cls._connect()

        try:
            row = await connection.fetchrow(
                """
                UPDATE ops_actions
                SET
                    status = $2,
                    result = $3::jsonb,
                    error = $4,
                    completed_at = NOW()
                WHERE id = $1
                RETURNING *
                """,
                action_id,
                status,
                result or {},
                error,
            )
        finally:
            await connection.close()

        return cls._action(row)

    @staticmethod
    def _incident(row) -> IncidentRecord:
        return IncidentRecord(
            id=row["id"],
            service=row["service"],
            summary=row["summary"],
            severity=row["severity"],
            status=row["status"],
            source=row["source"],
            diagnosis=row["diagnosis"] or {},
            metadata=row["metadata"] or {},
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            resolved_at=row["resolved_at"],
        )

    @staticmethod
    def _action(row) -> OpsActionRecord:
        return OpsActionRecord(
            id=row["id"],
            incident_id=row["incident_id"],
            action=row["action"],
            target=row["target"],
            status=row["status"],
            approved=row["approved"],
            reason=row["reason"],
            result=row["result"] or {},
            error=row["error"],
            created_at=row["created_at"],
            completed_at=row["completed_at"],
            idempotency_key=row.get("idempotency_key"),
            duplicate_detected=bool(row.get("duplicate_detected", False)),
        )