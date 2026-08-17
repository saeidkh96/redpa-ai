from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.guardrails.contracts import GuardrailDecision, GuardrailEvaluation, RiskLevel
from app.models.policy_override_v10 import PolicyOverrideV10
from app.schemas.policy_overrides_v10 import PolicyOverrideCreate, PolicyOverrideUpdate


class PolicyOverrideNotFoundError(Exception):
    pass


class PolicyOverrideConflictError(Exception):
    pass


class PolicyOverrideV10Service:
    VERSION = "10.2"

    @staticmethod
    def _normalize(value: str) -> str:
        return value.strip().lower().replace("-", "_")

    async def list(self, *, session: AsyncSession, user_id: uuid.UUID) -> list[PolicyOverrideV10]:
        result = await session.execute(
            select(PolicyOverrideV10)
            .where(PolicyOverrideV10.user_id == user_id)
            .order_by(PolicyOverrideV10.boundary, PolicyOverrideV10.action)
        )
        return list(result.scalars().all())

    async def create(
        self, *, session: AsyncSession, user_id: uuid.UUID, payload: PolicyOverrideCreate
    ) -> PolicyOverrideV10:
        boundary = self._normalize(payload.boundary)
        action = self._normalize(payload.action)
        existing = await self.match_record(
            session=session, user_id=user_id, boundary=boundary, action=action, enabled_only=False
        )
        if existing is not None:
            raise PolicyOverrideConflictError("A policy override already exists for this action and boundary.")

        record = PolicyOverrideV10(
            user_id=user_id,
            boundary=boundary,
            action=action,
            resource=payload.resource,
            decision=payload.decision.value,
            risk=payload.risk.value,
            reason=payload.reason.strip(),
            enabled=payload.enabled,
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return record

    async def update(
        self, *, session: AsyncSession, user_id: uuid.UUID, override_id: uuid.UUID,
        payload: PolicyOverrideUpdate,
    ) -> PolicyOverrideV10:
        record = await self.get(session=session, user_id=user_id, override_id=override_id)
        if payload.resource is not None:
            record.resource = payload.resource
        if payload.decision is not None:
            record.decision = payload.decision.value
        if payload.risk is not None:
            record.risk = payload.risk.value
        if payload.reason is not None:
            record.reason = payload.reason.strip()
        if payload.enabled is not None:
            record.enabled = payload.enabled
        await session.commit()
        await session.refresh(record)
        return record

    async def delete(
        self, *, session: AsyncSession, user_id: uuid.UUID, override_id: uuid.UUID
    ) -> None:
        record = await self.get(session=session, user_id=user_id, override_id=override_id)
        await session.delete(record)
        await session.commit()

    async def get(
        self, *, session: AsyncSession, user_id: uuid.UUID, override_id: uuid.UUID
    ) -> PolicyOverrideV10:
        result = await session.execute(
            select(PolicyOverrideV10).where(
                PolicyOverrideV10.id == override_id,
                PolicyOverrideV10.user_id == user_id,
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            raise PolicyOverrideNotFoundError("Policy override not found.")
        return record

    async def match_record(
        self, *, session: AsyncSession, user_id: uuid.UUID, boundary: str,
        action: str, enabled_only: bool = True,
    ) -> PolicyOverrideV10 | None:
        filters = [
            PolicyOverrideV10.user_id == user_id,
            PolicyOverrideV10.boundary == self._normalize(boundary),
            PolicyOverrideV10.action == self._normalize(action),
        ]
        if enabled_only:
            filters.append(PolicyOverrideV10.enabled.is_(True))
        result = await session.execute(select(PolicyOverrideV10).where(*filters))
        return result.scalar_one_or_none()

    async def evaluate(
        self, *, session: AsyncSession, user_id: uuid.UUID, boundary: str, action: str,
        resource: str | None,
    ) -> GuardrailEvaluation | None:
        record = await self.match_record(
            session=session, user_id=user_id, boundary=boundary, action=action
        )
        if record is None:
            return None
        if record.resource and resource and record.resource != resource:
            return None
        return GuardrailEvaluation(
            decision=GuardrailDecision(record.decision),
            risk=RiskLevel(record.risk),
            reason=record.reason,
            matched_rules=(f"USER_OVERRIDE:{record.id}",),
            policy_version=self.VERSION,
            source="redpa-policy-override",
        )


policy_override_v10_service = PolicyOverrideV10Service()
