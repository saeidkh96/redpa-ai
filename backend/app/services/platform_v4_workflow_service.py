from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from prometheus_client import Counter, Gauge
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.contracts import EventEnvelope
from app.models.platform_v4_control import (
    PlatformWorkflowCheckpoint,
    PlatformWorkflowDefinition,
    PlatformWorkflowRun,
)
from app.services.event_outbox_service import EventOutboxService


WORKFLOW_TRANSITIONS_TOTAL = Counter(
    "redpa_platform_workflow_transitions_total",
    "v4 workflow lifecycle transitions.",
    ("from_status", "to_status"),
)
WORKFLOWS_IN_PROGRESS = Gauge(
    "redpa_platform_workflows_in_progress",
    "v4 workflows currently in running or paused state.",
)


class PlatformWorkflowNotFoundError(LookupError):
    pass


class PlatformWorkflowTransitionError(ValueError):
    pass


ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "running": frozenset({"paused", "completed", "failed", "cancelled"}),
    "paused": frozenset({"running", "cancelled", "failed"}),
    "failed": frozenset({"running", "cancelled"}),
    "completed": frozenset(),
    "cancelled": frozenset(),
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PlatformWorkflowService:
    @staticmethod
    async def create_definition(
        *,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        name: str,
        version: str,
        definition: dict[str, Any],
        created_by: uuid.UUID,
    ) -> PlatformWorkflowDefinition:
        if not name.strip() or not version.strip():
            raise ValueError("Workflow name and version are required.")

        row = PlatformWorkflowDefinition(
            tenant_id=tenant_id,
            name=name.strip(),
            version=version.strip(),
            definition=definition,
            created_by=created_by,
        )
        session.add(row)
        await session.flush()
        await EventOutboxService.enqueue(
            session=session,
            event=EventEnvelope(
                event_type="platform.workflow_definition.created",
                aggregate_type="workflow_definition",
                aggregate_id=str(row.id),
                tenant_id=tenant_id,
                payload={"name": row.name, "version": row.version},
            ),
            commit=False,
        )
        await session.commit()
        await session.refresh(row)
        return row

    @staticmethod
    async def list_definitions(
        *,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        limit: int = 100,
    ) -> list[PlatformWorkflowDefinition]:
        result = await session.execute(
            select(PlatformWorkflowDefinition)
            .where(PlatformWorkflowDefinition.tenant_id == tenant_id)
            .order_by(PlatformWorkflowDefinition.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def start_run(
        *,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        workflow_name: str,
        workflow_version: str,
        created_by: uuid.UUID,
        definition_id: uuid.UUID | None = None,
        input_payload: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> PlatformWorkflowRun:
        if definition_id is not None:
            definition_result = await session.execute(
                select(PlatformWorkflowDefinition).where(
                    PlatformWorkflowDefinition.id == definition_id,
                    PlatformWorkflowDefinition.tenant_id == tenant_id,
                )
            )
            if definition_result.scalar_one_or_none() is None:
                raise PlatformWorkflowNotFoundError(
                    f"Workflow definition was not found for tenant: {definition_id}"
                )

        row = PlatformWorkflowRun(
            tenant_id=tenant_id,
            definition_id=definition_id,
            workflow_name=workflow_name,
            workflow_version=workflow_version,
            status="running",
            attempts=1,
            input_payload=input_payload or {},
            correlation_id=correlation_id,
            created_by=created_by,
        )
        session.add(row)
        await session.flush()
        await EventOutboxService.enqueue(
            session=session,
            event=EventEnvelope(
                event_type="platform.workflow.started",
                aggregate_type="workflow_run",
                aggregate_id=str(row.id),
                tenant_id=tenant_id,
                correlation_id=correlation_id,
                payload={"workflow": workflow_name, "version": workflow_version},
            ),
            commit=False,
        )
        await session.commit()
        await session.refresh(row)
        WORKFLOWS_IN_PROGRESS.inc()
        return row

    @staticmethod
    async def get_run(
        *,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        run_id: uuid.UUID,
        lock: bool = False,
    ) -> PlatformWorkflowRun:
        query = select(PlatformWorkflowRun).where(
            PlatformWorkflowRun.id == run_id,
            PlatformWorkflowRun.tenant_id == tenant_id,
        )
        if lock:
            query = query.with_for_update()
        result = await session.execute(query)
        row = result.scalar_one_or_none()
        if row is None:
            raise PlatformWorkflowNotFoundError(str(run_id))
        return row

    @staticmethod
    async def list_runs(
        *,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        status: str | None = None,
        limit: int = 100,
    ) -> list[PlatformWorkflowRun]:
        query = select(PlatformWorkflowRun).where(PlatformWorkflowRun.tenant_id == tenant_id)
        if status:
            query = query.where(PlatformWorkflowRun.status == status)
        result = await session.execute(query.order_by(PlatformWorkflowRun.created_at.desc()).limit(limit))
        return list(result.scalars().all())

    @classmethod
    async def checkpoint(
        cls,
        *,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        run_id: uuid.UUID,
        checkpoint_key: str,
        state: dict[str, Any],
        reason: str | None = None,
    ) -> PlatformWorkflowCheckpoint:
        run = await cls.get_run(session=session, tenant_id=tenant_id, run_id=run_id, lock=True)
        if run.status not in {"running", "paused"}:
            raise PlatformWorkflowTransitionError("Only running or paused workflows can checkpoint.")

        seq_result = await session.execute(
            select(func.coalesce(func.max(PlatformWorkflowCheckpoint.sequence), 0)).where(
                PlatformWorkflowCheckpoint.run_id == run_id
            )
        )
        sequence = int(seq_result.scalar_one()) + 1
        checkpoint = PlatformWorkflowCheckpoint(
            run_id=run_id,
            sequence=sequence,
            checkpoint_key=checkpoint_key,
            state=state,
            reason=reason,
        )
        session.add(checkpoint)
        run.current_checkpoint = checkpoint_key
        await session.flush()
        await EventOutboxService.enqueue(
            session=session,
            event=EventEnvelope(
                event_type="platform.workflow.checkpointed",
                aggregate_type="workflow_run",
                aggregate_id=str(run.id),
                tenant_id=tenant_id,
                correlation_id=run.correlation_id,
                payload={"checkpoint": checkpoint_key, "sequence": sequence, "reason": reason},
            ),
            commit=False,
        )
        await session.commit()
        await session.refresh(checkpoint)
        return checkpoint

    @classmethod
    async def transition(
        cls,
        *,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        run_id: uuid.UUID,
        to_status: str,
        reason: str,
        output_payload: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> PlatformWorkflowRun:
        run = await cls.get_run(session=session, tenant_id=tenant_id, run_id=run_id, lock=True)
        current = run.status
        target = to_status.strip().lower()
        if target not in ALLOWED_TRANSITIONS.get(current, frozenset()):
            raise PlatformWorkflowTransitionError(f"Invalid transition: {current} -> {target}")

        run.status = target
        run.updated_at = _now()
        if target == "running" and current in {"paused", "failed"}:
            run.attempts += 1
        if output_payload is not None:
            run.output_payload = output_payload
        if error is not None:
            run.last_error = error[:4000]
        if target == "completed":
            run.completed_at = _now()
            run.last_error = None
        elif target in {"failed", "cancelled"}:
            run.completed_at = _now()

        await EventOutboxService.enqueue(
            session=session,
            event=EventEnvelope(
                event_type=f"platform.workflow.{target}",
                aggregate_type="workflow_run",
                aggregate_id=str(run.id),
                tenant_id=tenant_id,
                correlation_id=run.correlation_id,
                payload={"from": current, "to": target, "reason": reason, "attempts": run.attempts},
            ),
            commit=False,
        )
        await session.commit()
        await session.refresh(run)

        WORKFLOW_TRANSITIONS_TOTAL.labels(from_status=current, to_status=target).inc()
        if current in {"running", "paused"} and target in {"completed", "failed", "cancelled"}:
            WORKFLOWS_IN_PROGRESS.dec()
        return run

    @staticmethod
    async def list_checkpoints(
        *,
        session: AsyncSession,
        run_id: uuid.UUID,
        limit: int = 200,
    ) -> list[PlatformWorkflowCheckpoint]:
        result = await session.execute(
            select(PlatformWorkflowCheckpoint)
            .where(PlatformWorkflowCheckpoint.run_id == run_id)
            .order_by(PlatformWorkflowCheckpoint.sequence.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
