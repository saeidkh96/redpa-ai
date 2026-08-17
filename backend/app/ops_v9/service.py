from __future__ import annotations
from uuid import UUID
import hashlib

from app.ops_v9.client import OpsAgentClient
from app.ops_v9.repository import OpsRepository
from app.ops_v9.schemas import RemediationRequest
from app.ops_v9.governance import OpsGovernanceBridge
from sqlalchemy.ext.asyncio import AsyncSession


class OpsService:
    @staticmethod
    def _idempotency_key(*, incident_id: UUID, run_id: UUID, action: str, target: str, approved: bool, supplied: str | None) -> str:
        if supplied:
            return supplied
        raw = f"{incident_id}:{run_id}:{action}:{target}:{approved}".encode("utf-8")
        return "ops-" + hashlib.sha256(raw).hexdigest()

    @classmethod
    async def diagnose(cls, incident_id: UUID):
        incident = await OpsRepository.get_incident(incident_id)
        diagnosis = await OpsAgentClient().diagnose(incident.service)
        return await OpsRepository.set_diagnosis(incident_id, diagnosis)

    @classmethod
    async def remediate(cls, incident_id: UUID, payload: RemediationRequest):
        incident = await OpsRepository.get_incident(incident_id)
        action = await OpsRepository.create_action(
            incident_id, action=payload.action, target=incident.service,
            approved=payload.approved, reason=payload.reason,
        )
        if not payload.approved:
            return await OpsRepository.finish_action(
                action.id, status='denied', error='Human approval is required for side effects.'
            )
        await OpsRepository.set_incident_status(incident_id, 'mitigating')
        try:
            result = await OpsAgentClient().restart(incident.service, approved=True, reason=payload.reason)
            finished = await OpsRepository.finish_action(action.id, status='completed', result=result)
            await OpsRepository.set_incident_status(incident_id, 'resolved')
            return finished
        except Exception as exc:
            await OpsRepository.set_incident_status(incident_id, 'failed')
            return await OpsRepository.finish_action(action.id, status='failed', error=str(exc))

    @classmethod
    async def diagnose_governed(cls, incident_id: UUID, *, session: AsyncSession, user_id: UUID, run_id: UUID):
        incident = await OpsRepository.get_incident(incident_id)
        await OpsGovernanceBridge.event(
            session=session, user_id=user_id, run_id=run_id,
            event_type="ops.diagnosis_started", stage="ops.diagnosis",
            payload={"incident_id": str(incident_id), "service": incident.service},
        )
        diagnosis = await OpsAgentClient().diagnose(incident.service)
        diagnosed = await OpsRepository.set_diagnosis(incident_id, diagnosis)
        await OpsGovernanceBridge.event(
            session=session, user_id=user_id, run_id=run_id,
            event_type="ops.diagnosis_completed", stage="ops.diagnosis",
            payload={"incident_id": str(incident_id), "diagnosis": diagnosis},
        )
        return diagnosed

    @classmethod
    async def remediate_governed(cls, incident_id: UUID, payload: RemediationRequest, *,
                                 session: AsyncSession, user_id: UUID, run_id: UUID):
        incident = await OpsRepository.get_incident(incident_id)
        policy = await OpsGovernanceBridge.remediation_policy(
            session=session, user_id=user_id, run_id=run_id, incident=incident,
            action=payload.action, reason=payload.reason, approved=payload.approved,
        )

        idempotency_key = cls._idempotency_key(
            incident_id=incident_id, run_id=run_id, action=payload.action,
            target=incident.service, approved=payload.approved, supplied=payload.idempotency_key,
        )
        action = await OpsRepository.create_action(
            incident_id, action=payload.action, target=incident.service,
            approved=payload.approved, reason=payload.reason,
            idempotency_key=idempotency_key,
        )

        # A duplicate request returns the already persisted terminal result and never
        # repeats the destructive side effect.
        if action.duplicate_detected:
            return action

        if not payload.approved or not policy.executable:
            await OpsGovernanceBridge.event(
                session=session, user_id=user_id, run_id=run_id,
                event_type="ops.remediation_blocked", stage="ops.remediation",
                payload={"incident_id": str(incident_id), "action": payload.action,
                         "target": incident.service, "approved": payload.approved,
                         "policy_decision": policy.decision, "policy_reason": policy.reason,
                         "idempotency_key": idempotency_key},
            )
            return await OpsRepository.finish_action(
                action.id, status="denied",
                error="Governance policy or human approval blocked the remediation."
            )

        await OpsGovernanceBridge.event(
            session=session, user_id=user_id, run_id=run_id,
            event_type="human.approval_granted", stage="governance.approval",
            payload={"incident_id": str(incident_id), "action": payload.action,
                     "target": incident.service, "approved": True,
                     "actor_user_id": str(user_id), "idempotency_key": idempotency_key},
        )
        await OpsGovernanceBridge.resume_after_approval(
            session=session, user_id=user_id, run_id=run_id
        )
        await OpsGovernanceBridge.event(
            session=session, user_id=user_id, run_id=run_id,
            event_type="run.resumed", stage="lifecycle",
            payload={"incident_id": str(incident_id), "reason": "human_approval"},
        )
        await OpsGovernanceBridge.event(
            session=session, user_id=user_id, run_id=run_id,
            event_type="ops.remediation_started", stage="ops.remediation",
            payload={"incident_id": str(incident_id), "action": payload.action,
                     "target": incident.service, "idempotency_key": idempotency_key},
        )
        await OpsRepository.set_incident_status(incident_id, "mitigating")
        try:
            result = await OpsAgentClient().restart(
                incident.service, approved=True, reason=payload.reason
            )
            verification = await OpsAgentClient().wait_until_healthy(incident.service)
        except Exception as exc:
            failed = await OpsRepository.set_incident_status(incident_id, "failed")
            await OpsGovernanceBridge.event(
                session=session, user_id=user_id, run_id=run_id,
                event_type="ops.recovery_failed", stage="ops.recovery",
                payload={"incident_id": str(incident_id), "action": payload.action,
                         "target": incident.service, "error": str(exc),
                         "idempotency_key": idempotency_key},
            )
            await OpsGovernanceBridge.finish(
                session=session, user_id=user_id, run_id=run_id, incident=failed,
                success=False, action=payload.action, error=str(exc),
            )
            return await OpsRepository.finish_action(
                action.id, status="failed", error=str(exc)
            )

        result = {**result, "verification": verification}
        finished = await OpsRepository.finish_action(
            action.id, status="completed", result=result
        )
        resolved = await OpsRepository.set_incident_status(incident_id, 'resolved')
        await OpsGovernanceBridge.event(
            session=session, user_id=user_id, run_id=run_id,
            event_type="ops.recovery_verified", stage="ops.recovery",
            payload={"incident_id": str(incident_id), "action": payload.action,
                     "target": incident.service, "result": result,
                     "health": verification.get("health"),
                     "state": verification.get("state"),
                     "idempotency_key": idempotency_key},
        )
        try:
            await OpsGovernanceBridge.finish(
                session=session, user_id=user_id, run_id=run_id, incident=resolved,
                success=True, action=payload.action,
            )
        except Exception as exc:
            await OpsGovernanceBridge.event(
                session=session, user_id=user_id, run_id=run_id,
                event_type="ops.governance_finalization_failed",
                stage="ops.governance",
                payload={"incident_id": str(incident_id), "action": payload.action,
                         "target": incident.service, "error": str(exc),
                         "recovery_verified": True},
            )
            raise
        return finished
