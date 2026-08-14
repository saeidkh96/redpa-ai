from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from uuid import UUID, uuid4

import asyncpg

from app.research_workspace.schemas import (
    EnterpriseResearchRun,
    EnterpriseResearchRunDetail,
    ResearchEvidenceItem,
    ResearchQuality,
    ResearchTimelineEvent,
)


class ResearchRunNotFoundError(LookupError):
    pass


class EnterpriseResearchRepository:
    @staticmethod
    def _database_url() -> str:
        value = os.getenv("DATABASE_URL", "").strip()
        if not value:
            raise RuntimeError(
                "DATABASE_URL is required for enterprise research runs."
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
    async def create_run(
        cls,
        *,
        query: str,
        max_results: int,
        minimum_quality_score: float,
    ) -> UUID:
        run_id = uuid4()
        now = datetime.now(timezone.utc)
        connection = await cls._connect()
        try:
            await connection.execute(
                """
                INSERT INTO enterprise_research_runs (
                    id, query, status, current_stage, progress,
                    max_results, minimum_quality_score,
                    evidence, created_at, updated_at
                )
                VALUES (
                    $1, $2, 'queued', 'queued', 0,
                    $3, $4, '[]'::jsonb, $5, $5
                )
                """,
                run_id,
                query,
                max_results,
                minimum_quality_score,
                now,
            )
        finally:
            await connection.close()

        await cls.add_event(
            run_id,
            stage="queued",
            status="completed",
            message="Research run queued.",
        )
        return run_id

    @classmethod
    async def update_run(
        cls,
        run_id: UUID,
        *,
        status: str,
        current_stage: str,
        progress: int,
        provider: str | None = None,
        report: str | None = None,
        evidence: list[dict] | None = None,
        quality: dict | None = None,
        error: str | None = None,
        completed: bool = False,
    ) -> None:
        connection = await cls._connect()
        try:
            result = await connection.execute(
                """
                UPDATE enterprise_research_runs
                SET status = $2,
                    current_stage = $3,
                    progress = $4,
                    provider = COALESCE($5, provider),
                    report = COALESCE($6, report),
                    evidence = COALESCE($7::jsonb, evidence),
                    quality = COALESCE($8::jsonb, quality),
                    error = $9,
                    updated_at = NOW(),
                    completed_at = CASE
                        WHEN $10 THEN NOW()
                        ELSE completed_at
                    END
                WHERE id = $1
                """,
                run_id,
                status,
                current_stage,
                progress,
                provider,
                report,
                evidence,
                quality,
                error,
                completed,
            )
            if result.endswith("0"):
                raise ResearchRunNotFoundError(
                    f"Research run was not found: {run_id}"
                )
        finally:
            await connection.close()

    @classmethod
    async def add_event(
        cls,
        run_id: UUID,
        *,
        stage: str,
        status: str,
        message: str,
        metadata: dict | None = None,
    ) -> None:
        connection = await cls._connect()
        try:
            await connection.execute(
                """
                INSERT INTO enterprise_research_events (
                    id, run_id, stage, status,
                    message, metadata, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6::jsonb, NOW())
                """,
                uuid4(),
                run_id,
                stage,
                status,
                message,
                metadata or {},
            )
        finally:
            await connection.close()

    @classmethod
    async def get_run(
        cls,
        run_id: UUID,
        *,
        include_timeline: bool = True,
    ) -> EnterpriseResearchRunDetail:
        connection = await cls._connect()
        try:
            row = await connection.fetchrow(
                """
                SELECT *
                FROM enterprise_research_runs
                WHERE id = $1
                """,
                run_id,
            )
            if row is None:
                raise ResearchRunNotFoundError(
                    f"Research run was not found: {run_id}"
                )

            events = []
            if include_timeline:
                events = await connection.fetch(
                    """
                    SELECT *
                    FROM enterprise_research_events
                    WHERE run_id = $1
                    ORDER BY created_at, id
                    """,
                    run_id,
                )
        finally:
            await connection.close()

        return cls._row_to_detail(row, events)

    @classmethod
    async def list_runs(
        cls,
        *,
        limit: int = 50,
    ) -> list[EnterpriseResearchRun]:
        connection = await cls._connect()
        try:
            rows = await connection.fetch(
                """
                SELECT *
                FROM enterprise_research_runs
                ORDER BY created_at DESC
                LIMIT $1
                """,
                limit,
            )
        finally:
            await connection.close()

        return [
            cls._row_to_run(row)
            for row in rows
        ]

    @staticmethod
    def _row_to_run(row) -> EnterpriseResearchRun:
        evidence_payload = row["evidence"] or []
        quality_payload = row["quality"]

        return EnterpriseResearchRun(
            id=row["id"],
            query=row["query"],
            status=row["status"],
            current_stage=row["current_stage"],
            progress=row["progress"],
            max_results=row["max_results"],
            minimum_quality_score=row["minimum_quality_score"],
            provider=row["provider"],
            report=row["report"],
            evidence=[
                ResearchEvidenceItem.model_validate(item)
                for item in evidence_payload
            ],
            quality=(
                ResearchQuality.model_validate(quality_payload)
                if quality_payload
                else None
            ),
            error=row["error"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            completed_at=row["completed_at"],
        )

    @classmethod
    def _row_to_detail(
        cls,
        row,
        event_rows,
    ) -> EnterpriseResearchRunDetail:
        base = cls._row_to_run(row)
        return EnterpriseResearchRunDetail(
            **base.model_dump(),
            timeline=[
                ResearchTimelineEvent(
                    id=event["id"],
                    stage=event["stage"],
                    status=event["status"],
                    message=event["message"],
                    metadata=event["metadata"] or {},
                    created_at=event["created_at"],
                )
                for event in event_rows
            ],
        )
