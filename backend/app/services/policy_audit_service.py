from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.guardrails.contracts import GuardrailEvaluation
from app.models.policy_audit_event import PolicyAuditEvent


logger = logging.getLogger(__name__)


class PolicyAuditService:
    @staticmethod
    async def record(
        *,
        session: AsyncSession,
        boundary: str,
        action: str,
        evaluation: GuardrailEvaluation,
        user_id: uuid.UUID | None = None,
        conversation_id: uuid.UUID | None = None,
        review_id: uuid.UUID | None = None,
        resource: str | None = None,
        metadata: dict[str, Any] | None = None,
        commit: bool = False,
    ) -> PolicyAuditEvent:
        event = PolicyAuditEvent(
            user_id=user_id,
            conversation_id=conversation_id,
            review_id=review_id,
            boundary=boundary,
            action=action,
            resource=resource,
            decision=evaluation.decision.value,
            risk=evaluation.risk.value,
            reason=evaluation.reason,
            matched_rules=list(evaluation.matched_rules),
            policy_version=evaluation.policy_version,
            source=evaluation.source,
            event_metadata=metadata or {},
        )
        session.add(event)

        if commit:
            await session.commit()
            await session.refresh(event)
        else:
            await session.flush()

        logger.info(
            "Policy audit | boundary=%s action=%s decision=%s risk=%s "
            "policy_version=%s review_id=%s",
            boundary,
            action,
            evaluation.decision.value,
            evaluation.risk.value,
            evaluation.policy_version,
            review_id,
        )

        return event

    @staticmethod
    async def list_for_user(
        *,
        session: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 100,
    ) -> list[PolicyAuditEvent]:
        result = await session.execute(
            select(PolicyAuditEvent)
            .where(PolicyAuditEvent.user_id == user_id)
            .order_by(PolicyAuditEvent.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
