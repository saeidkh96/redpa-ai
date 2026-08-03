from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import asyncpg

from app.distributed_durable.schemas import (
    DurableSubtaskRecord,
    DurableWorkflowRecord,
)
from app.distributed_multi.schemas import (
    DistributedSubtask,
    DistributedSubtaskResult,
)


class DurableWorkflowNotFoundError(LookupError):
    pass


class DurableWorkflowRepository:
    @staticmethod
    def _database_url() -> str:
        value = os.getenv(
            "DATABASE_URL",
            "",
        ).strip()

        if not value:
            raise RuntimeError(
                "DATABASE_URL is required for durable workflows."
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

    @staticmethod
    def _normalize_metadata(
        value: Any,
    ) -> dict[str, Any]:
        if value is None:
            return {}

        if isinstance(
            value,
            dict,
        ):
            return value

        if isinstance(
            value,
            str,
        ):
            stripped = value.strip()

            if not stripped:
                return {}

            try:
                parsed = json.loads(
                    stripped,
                )
            except json.JSONDecodeError:
                return {
                    "raw": stripped,
                }

            if isinstance(
                parsed,
                dict,
            ):
                return parsed

            return {
                "value": parsed,
            }

        try:
            return dict(
                value,
            )
        except (
            TypeError,
            ValueError,
        ):
            return {
                "value": value,
            }

    @classmethod
    async def ensure_schema(cls) -> None:
        connection = await cls._connect()

        try:
            await connection.execute(
                """
                CREATE TABLE IF NOT EXISTS distributed_workflows (
                    id UUID PRIMARY KEY,
                    request TEXT NOT NULL,
                    status VARCHAR(32) NOT NULL,
                    approval_required BOOLEAN NOT NULL DEFAULT FALSE,
                    approval_granted BOOLEAN NOT NULL DEFAULT FALSE,
                    review_reason TEXT NULL,
                    max_parallelism INTEGER NOT NULL,
                    timeout_seconds DOUBLE PRECISION NOT NULL,
                    aggregated_response TEXT NULL,
                    successful_subtasks INTEGER NOT NULL DEFAULT 0,
                    failed_subtasks INTEGER NOT NULL DEFAULT 0,
                    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL,
                    completed_at TIMESTAMPTZ NULL
                )
                """
            )

            await connection.execute(
                """
                CREATE TABLE IF NOT EXISTS distributed_workflow_subtasks (
                    id UUID PRIMARY KEY,
                    workflow_id UUID NOT NULL
                        REFERENCES distributed_workflows(id)
                        ON DELETE CASCADE,
                    subtask_key VARCHAR(100) NOT NULL,
                    instruction TEXT NOT NULL,
                    status VARCHAR(32) NOT NULL,
                    remote_agent VARCHAR(255) NULL,
                    selected_skill VARCHAR(255) NULL,
                    response TEXT NULL,
                    task_id VARCHAR(255) NULL,
                    context_id VARCHAR(255) NULL,
                    execution_time_ms DOUBLE PRECISION NOT NULL DEFAULT 0,
                    error TEXT NULL,
                    attempt_count INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL,
                    UNIQUE(workflow_id, subtask_key)
                )
                """
            )

            await connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                ix_distributed_workflows_status
                ON distributed_workflows(status)
                """
            )

            await connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                ix_distributed_subtasks_workflow_status
                ON distributed_workflow_subtasks(
                    workflow_id,
                    status
                )
                """
            )

        finally:
            await connection.close()

    @classmethod
    async def create_workflow(
        cls,
        *,
        request: str,
        subtasks: list[DistributedSubtask],
        max_parallelism: int,
        timeout_seconds: float,
        approval_granted: bool,
    ) -> UUID:
        await cls.ensure_schema()

        workflow_id = uuid4()
        now = datetime.now(timezone.utc)
        connection = await cls._connect()

        try:
            async with connection.transaction():
                await connection.execute(
                    """
                    INSERT INTO distributed_workflows (
                        id,
                        request,
                        status,
                        approval_required,
                        approval_granted,
                        max_parallelism,
                        timeout_seconds,
                        metadata,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        $1, $2, 'pending', FALSE, $3,
                        $4, $5, $6::jsonb, $7, $7
                    )
                    """,
                    workflow_id,
                    request,
                    approval_granted,
                    max_parallelism,
                    timeout_seconds,
                    {},
                    now,
                )

                for subtask in subtasks:
                    await connection.execute(
                        """
                        INSERT INTO distributed_workflow_subtasks (
                            id,
                            workflow_id,
                            subtask_key,
                            instruction,
                            status,
                            created_at,
                            updated_at
                        )
                        VALUES (
                            $1, $2, $3, $4,
                            'pending', $5, $5
                        )
                        """,
                        uuid4(),
                        workflow_id,
                        subtask.id,
                        subtask.instruction,
                        now,
                    )

        finally:
            await connection.close()

        return workflow_id

    @classmethod
    async def mark_workflow_running(
        cls,
        workflow_id: UUID,
        *,
        approval_granted: bool,
    ) -> None:
        await cls.ensure_schema()
        connection = await cls._connect()

        try:
            result = await connection.execute(
                """
                UPDATE distributed_workflows
                SET
                    status = 'running',
                    approval_granted = $2,
                    approval_required = FALSE,
                    review_reason = NULL,
                    updated_at = NOW()
                WHERE id = $1
                """,
                workflow_id,
                approval_granted,
            )

            if result.endswith("0"):
                raise DurableWorkflowNotFoundError(
                    f"Workflow was not found: {workflow_id}"
                )

        finally:
            await connection.close()

    @classmethod
    async def mark_approval_required(
        cls,
        workflow_id: UUID,
        *,
        reason: str | None,
    ) -> None:
        connection = await cls._connect()

        try:
            await connection.execute(
                """
                UPDATE distributed_workflows
                SET
                    status = 'approval_required',
                    approval_required = TRUE,
                    review_reason = $2,
                    updated_at = NOW()
                WHERE id = $1
                """,
                workflow_id,
                reason,
            )

        finally:
            await connection.close()

    @classmethod
    async def mark_subtasks_running(
        cls,
        workflow_id: UUID,
        subtask_keys: list[str],
    ) -> None:
        if not subtask_keys:
            return

        connection = await cls._connect()

        try:
            await connection.execute(
                """
                UPDATE distributed_workflow_subtasks
                SET
                    status = 'running',
                    attempt_count = attempt_count + 1,
                    error = NULL,
                    updated_at = NOW()
                WHERE workflow_id = $1
                  AND subtask_key = ANY($2::varchar[])
                """,
                workflow_id,
                subtask_keys,
            )

        finally:
            await connection.close()

    @classmethod
    async def save_subtask_results(
        cls,
        workflow_id: UUID,
        results: list[DistributedSubtaskResult],
    ) -> None:
        if not results:
            return

        connection = await cls._connect()

        try:
            async with connection.transaction():
                for result in results:
                    await connection.execute(
                        """
                        UPDATE distributed_workflow_subtasks
                        SET
                            status = $3,
                            remote_agent = $4,
                            selected_skill = $5,
                            response = $6,
                            task_id = $7,
                            context_id = $8,
                            execution_time_ms = $9,
                            error = $10,
                            updated_at = NOW()
                        WHERE workflow_id = $1
                          AND subtask_key = $2
                        """,
                        workflow_id,
                        result.subtask_id,
                        (
                            "completed"
                            if result.success
                            else "failed"
                        ),
                        result.remote_agent,
                        result.selected_skill,
                        result.response,
                        result.task_id,
                        result.context_id,
                        result.execution_time_ms,
                        result.error,
                    )

        finally:
            await connection.close()

    @classmethod
    async def finalize_workflow(
        cls,
        workflow_id: UUID,
        *,
        status: str,
        aggregated_response: str,
        successful_subtasks: int,
        failed_subtasks: int,
        metadata: dict[str, Any],
    ) -> None:
        connection = await cls._connect()

        try:
            await connection.execute(
                """
                UPDATE distributed_workflows
                SET
                    status = $2::varchar,
                    aggregated_response = $3,
                    successful_subtasks = $4,
                    failed_subtasks = $5,
                    metadata = $6::jsonb,
                    updated_at = NOW(),
                    completed_at = CASE
                        WHEN $2::varchar IN ('completed', 'partial', 'failed')
                        THEN NOW()
                        ELSE completed_at
                    END
                WHERE id = $1
                """,
                workflow_id,
                status,
                aggregated_response,
                successful_subtasks,
                failed_subtasks,
                metadata,
            )

        finally:
            await connection.close()

    @classmethod
    async def get_workflow(
        cls,
        workflow_id: UUID,
    ) -> DurableWorkflowRecord:
        await cls.ensure_schema()
        connection = await cls._connect()

        try:
            workflow = await connection.fetchrow(
                """
                SELECT *
                FROM distributed_workflows
                WHERE id = $1
                """,
                workflow_id,
            )

            if workflow is None:
                raise DurableWorkflowNotFoundError(
                    f"Workflow was not found: {workflow_id}"
                )

            subtask_rows = await connection.fetch(
                """
                SELECT *
                FROM distributed_workflow_subtasks
                WHERE workflow_id = $1
                ORDER BY created_at, subtask_key
                """,
                workflow_id,
            )

        finally:
            await connection.close()

        return DurableWorkflowRecord(
            id=workflow["id"],
            request=workflow["request"],
            status=workflow["status"],
            approval_required=workflow["approval_required"],
            approval_granted=workflow["approval_granted"],
            review_reason=workflow["review_reason"],
            max_parallelism=workflow["max_parallelism"],
            timeout_seconds=workflow["timeout_seconds"],
            aggregated_response=workflow["aggregated_response"],
            successful_subtasks=workflow["successful_subtasks"],
            failed_subtasks=workflow["failed_subtasks"],
            metadata=cls._normalize_metadata(
                workflow["metadata"],
            ),
            created_at=workflow["created_at"],
            updated_at=workflow["updated_at"],
            completed_at=workflow["completed_at"],
            subtasks=[
                DurableSubtaskRecord(
                    id=row["id"],
                    workflow_id=row["workflow_id"],
                    subtask_key=row["subtask_key"],
                    instruction=row["instruction"],
                    status=row["status"],
                    remote_agent=row["remote_agent"],
                    selected_skill=row["selected_skill"],
                    response=row["response"],
                    task_id=row["task_id"],
                    context_id=row["context_id"],
                    execution_time_ms=row["execution_time_ms"],
                    error=row["error"],
                    attempt_count=row["attempt_count"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in subtask_rows
            ],
        )

    @classmethod
    async def list_workflows(
        cls,
        *,
        limit: int = 50,
    ) -> list[DurableWorkflowRecord]:
        await cls.ensure_schema()
        connection = await cls._connect()

        try:
            rows = await connection.fetch(
                """
                SELECT id
                FROM distributed_workflows
                ORDER BY created_at DESC
                LIMIT $1
                """,
                limit,
            )

        finally:
            await connection.close()

        return [
            await cls.get_workflow(
                row["id"],
            )
            for row in rows
        ]
