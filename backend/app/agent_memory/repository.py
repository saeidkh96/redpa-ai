from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import asyncpg

from app.agent_memory.schemas import (
    MemoryCreate,
    MemoryRecord,
    MemoryUpdate,
)


class MemoryNotFoundError(LookupError):
    pass


class AgentMemoryRepository:
    @staticmethod
    def _database_url() -> str:
        value = os.getenv(
            "DATABASE_URL",
            "",
        ).strip()

        if not value:
            raise RuntimeError(
                "DATABASE_URL is required for agent memory."
            )

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
    async def ensure_schema(cls) -> None:
        connection = await cls._connect()

        try:
            await connection.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_memories (
                    id UUID PRIMARY KEY,
                    agent_id VARCHAR(100) NOT NULL,
                    content TEXT NOT NULL,
                    scope VARCHAR(32) NOT NULL,
                    kind VARCHAR(32) NOT NULL,
                    user_id UUID NULL,
                    workflow_id UUID NULL,
                    importance DOUBLE PRECISION NOT NULL DEFAULT 0.5,
                    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    embedding_status VARCHAR(32) NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL,
                    last_accessed_at TIMESTAMPTZ NULL
                )
                """
            )

            await connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                ix_agent_memories_agent_id
                ON agent_memories(agent_id)
                """
            )

            await connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                ix_agent_memories_user_id
                ON agent_memories(user_id)
                """
            )

            await connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                ix_agent_memories_workflow_id
                ON agent_memories(workflow_id)
                """
            )

            await connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                ix_agent_memories_scope_kind
                ON agent_memories(scope, kind)
                """
            )

            await connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                ix_agent_memories_active_created
                ON agent_memories(is_active, created_at DESC)
                """
            )

        finally:
            await connection.close()

    @classmethod
    async def create(
        cls,
        payload: MemoryCreate,
    ) -> MemoryRecord:
        await cls.ensure_schema()

        memory_id = uuid4()
        now = datetime.now(timezone.utc)
        connection = await cls._connect()

        try:
            row = await connection.fetchrow(
                """
                INSERT INTO agent_memories (
                    id,
                    agent_id,
                    content,
                    scope,
                    kind,
                    user_id,
                    workflow_id,
                    importance,
                    metadata,
                    is_active,
                    embedding_status,
                    created_at,
                    updated_at
                )
                VALUES (
                    $1, $2, $3, $4::varchar, $5::varchar,
                    $6, $7, $8, $9::jsonb, TRUE, 'pending',
                    $10, $10
                )
                RETURNING *
                """,
                memory_id,
                payload.agent_id,
                payload.content,
                payload.scope,
                payload.kind,
                payload.user_id,
                payload.workflow_id,
                payload.importance,
                payload.metadata,
                now,
            )

        finally:
            await connection.close()

        return cls._to_record(
            row,
        )

    @classmethod
    async def get(
        cls,
        memory_id: UUID,
    ) -> MemoryRecord:
        await cls.ensure_schema()
        connection = await cls._connect()

        try:
            row = await connection.fetchrow(
                """
                SELECT *
                FROM agent_memories
                WHERE id = $1
                """,
                memory_id,
            )

            if row is None:
                raise MemoryNotFoundError(
                    f"Memory was not found: {memory_id}"
                )

        finally:
            await connection.close()

        return cls._to_record(
            row,
        )

    @classmethod
    async def list(
        cls,
        *,
        agent_id: str | None = None,
        user_id: UUID | None = None,
        workflow_id: UUID | None = None,
        scope: str | None = None,
        kind: str | None = None,
        active_only: bool = True,
        limit: int = 100,
    ) -> list[MemoryRecord]:
        await cls.ensure_schema()
        connection = await cls._connect()

        try:
            rows = await connection.fetch(
                """
                SELECT *
                FROM agent_memories
                WHERE ($1::varchar IS NULL OR agent_id = $1)
                  AND ($2::uuid IS NULL OR user_id = $2)
                  AND ($3::uuid IS NULL OR workflow_id = $3)
                  AND ($4::varchar IS NULL OR scope = $4)
                  AND ($5::varchar IS NULL OR kind = $5)
                  AND ($6::boolean = FALSE OR is_active = TRUE)
                ORDER BY importance DESC, created_at DESC
                LIMIT $7
                """,
                agent_id,
                user_id,
                workflow_id,
                scope,
                kind,
                active_only,
                limit,
            )

        finally:
            await connection.close()

        return [
            cls._to_record(
                row,
            )
            for row in rows
        ]

    @classmethod
    async def update(
        cls,
        memory_id: UUID,
        payload: MemoryUpdate,
    ) -> MemoryRecord:
        current = await cls.get(
            memory_id,
        )

        content = (
            payload.content
            if payload.content is not None
            else current.content
        )

        scope = (
            payload.scope
            if payload.scope is not None
            else current.scope
        )

        kind = (
            payload.kind
            if payload.kind is not None
            else current.kind
        )

        importance = (
            payload.importance
            if payload.importance is not None
            else current.importance
        )

        metadata = (
            payload.metadata
            if payload.metadata is not None
            else current.metadata
        )

        is_active = (
            payload.is_active
            if payload.is_active is not None
            else current.is_active
        )

        embedding_status = (
            "pending"
            if payload.reembed
            and (
                payload.content is not None
                or payload.metadata is not None
            )
            else current.embedding_status
        )

        connection = await cls._connect()

        try:
            row = await connection.fetchrow(
                """
                UPDATE agent_memories
                SET
                    content = $2,
                    scope = $3::varchar,
                    kind = $4::varchar,
                    importance = $5,
                    metadata = $6::jsonb,
                    is_active = $7,
                    embedding_status = $8::varchar,
                    updated_at = NOW()
                WHERE id = $1
                RETURNING *
                """,
                memory_id,
                content,
                scope,
                kind,
                importance,
                metadata,
                is_active,
                embedding_status,
            )

        finally:
            await connection.close()

        return cls._to_record(
            row,
        )

    @classmethod
    async def set_embedding_status(
        cls,
        memory_id: UUID,
        status: str,
    ) -> None:
        connection = await cls._connect()

        try:
            await connection.execute(
                """
                UPDATE agent_memories
                SET
                    embedding_status = $2::varchar,
                    updated_at = NOW()
                WHERE id = $1
                """,
                memory_id,
                status,
            )

        finally:
            await connection.close()

    @classmethod
    async def touch(
        cls,
        memory_ids: list[UUID],
    ) -> None:
        if not memory_ids:
            return

        connection = await cls._connect()

        try:
            await connection.execute(
                """
                UPDATE agent_memories
                SET last_accessed_at = NOW()
                WHERE id = ANY($1::uuid[])
                """,
                memory_ids,
            )

        finally:
            await connection.close()

    @classmethod
    async def delete(
        cls,
        memory_id: UUID,
    ) -> None:
        connection = await cls._connect()

        try:
            result = await connection.execute(
                """
                DELETE FROM agent_memories
                WHERE id = $1
                """,
                memory_id,
            )

            if result.endswith("0"):
                raise MemoryNotFoundError(
                    f"Memory was not found: {memory_id}"
                )

        finally:
            await connection.close()

    @staticmethod
    def _to_record(
        row: asyncpg.Record,
    ) -> MemoryRecord:
        metadata = row["metadata"]

        if isinstance(
            metadata,
            str,
        ):
            metadata = json.loads(
                metadata,
            )

        return MemoryRecord(
            id=row["id"],
            agent_id=row["agent_id"],
            content=row["content"],
            scope=row["scope"],
            kind=row["kind"],
            user_id=row["user_id"],
            workflow_id=row["workflow_id"],
            importance=row["importance"],
            metadata=dict(
                metadata
                or {}
            ),
            is_active=row["is_active"],
            embedding_status=row["embedding_status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            last_accessed_at=row["last_accessed_at"],
        )
