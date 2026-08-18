from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.database.session import AsyncSessionFactory
from app.models.self_healing_v12 import SelfHealingCheckpoint


class FailoverCheckpointStore:
    """
    V12 Stage 9 PostgreSQL-backed failover persistence.

    Checkpoints survive:
      - backend restarts
      - scheduler restarts
      - process-local memory loss

    idempotency_key is the durable workflow identity.
    """

    @staticmethod
    def _uuid_or_none(
        value: Any,
    ) -> uuid.UUID | None:
        if value is None or value == "":
            return None

        if isinstance(value, uuid.UUID):
            return value

        try:
            return uuid.UUID(str(value))
        except ValueError:
            return None

    async def save(
        self,
        key: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        normalized_key = str(key or "").strip()

        if not normalized_key:
            raise ValueError(
                "Failover checkpoint idempotency key is required."
            )

        stage = str(
            payload.get("stage") or "unknown"
        ).strip()

        result = payload.get("result") or {}
        request = payload.get("request") or {}
        handoff = payload.get("handoff") or {}

        failed_agent_id = (
            payload.get("failed_agent_id")
            or request.get("failed_agent_id")
            or result.get("failed_agent_id")
            or handoff.get("source_agent_id")
        )

        replacement_agent_id = (
            payload.get("replacement_agent_id")
            or result.get("replacement_agent_id")
            or handoff.get("target_agent_id")
        )

        workflow_id = (
            payload.get("workflow_id")
            or request.get("workflow_id")
            or handoff.get("workflow_id")
        )

        run_id = self._uuid_or_none(
            payload.get("run_id")
            or request.get("run_id")
            or handoff.get("run_id")
        )

        now = datetime.now(timezone.utc)

        stmt = (
            insert(SelfHealingCheckpoint)
            .values(
                idempotency_key=normalized_key,
                stage=stage,
                failed_agent_id=failed_agent_id,
                replacement_agent_id=replacement_agent_id,
                workflow_id=workflow_id,
                run_id=run_id,
                payload=payload,
                created_at=now,
                updated_at=now,
            )
            .on_conflict_do_update(
                index_elements=[
                    SelfHealingCheckpoint.idempotency_key
                ],
                set_={
                    "stage": stage,
                    "failed_agent_id": failed_agent_id,
                    "replacement_agent_id": replacement_agent_id,
                    "workflow_id": workflow_id,
                    "run_id": run_id,
                    "payload": payload,
                    "updated_at": now,
                },
            )
            .returning(SelfHealingCheckpoint)
        )

        async with AsyncSessionFactory() as session:
            result_row = await session.execute(stmt)
            checkpoint = result_row.scalar_one()
            await session.commit()

        return {
            "id": str(checkpoint.id),
            "idempotency_key": checkpoint.idempotency_key,
            "stage": checkpoint.stage,
            "failed_agent_id": checkpoint.failed_agent_id,
            "replacement_agent_id": checkpoint.replacement_agent_id,
            "workflow_id": checkpoint.workflow_id,
            "run_id": (
                str(checkpoint.run_id)
                if checkpoint.run_id
                else None
            ),
            "payload": checkpoint.payload,
            "created_at": checkpoint.created_at.isoformat(),
            "updated_at": checkpoint.updated_at.isoformat(),
        }

    async def get(
        self,
        key: str,
    ) -> dict[str, Any] | None:
        normalized_key = str(key or "").strip()

        async with AsyncSessionFactory() as session:
            checkpoint = await session.scalar(
                select(SelfHealingCheckpoint).where(
                    SelfHealingCheckpoint.idempotency_key
                    == normalized_key
                )
            )

        if checkpoint is None:
            return None

        return {
            "id": str(checkpoint.id),
            "idempotency_key": checkpoint.idempotency_key,
            "stage": checkpoint.stage,
            "failed_agent_id": checkpoint.failed_agent_id,
            "replacement_agent_id": checkpoint.replacement_agent_id,
            "workflow_id": checkpoint.workflow_id,
            "run_id": (
                str(checkpoint.run_id)
                if checkpoint.run_id
                else None
            ),
            "payload": checkpoint.payload,
            "created_at": checkpoint.created_at.isoformat(),
            "updated_at": checkpoint.updated_at.isoformat(),
        }

    async def delete(
        self,
        key: str,
    ) -> None:
        normalized_key = str(key or "").strip()

        async with AsyncSessionFactory() as session:
            checkpoint = await session.scalar(
                select(SelfHealingCheckpoint).where(
                    SelfHealingCheckpoint.idempotency_key
                    == normalized_key
                )
            )

            if checkpoint is None:
                return

            await session.delete(checkpoint)
            await session.commit()


failover_checkpoint_store = FailoverCheckpointStore()