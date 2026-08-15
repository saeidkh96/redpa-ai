from __future__ import annotations
from uuid import UUID

from app.ops_v9.client import OpsAgentClient
from app.ops_v9.repository import OpsRepository
from app.ops_v9.schemas import RemediationRequest
from app.ops_v9.governance import OpsGovernanceBridge
from sqlalchemy.ext.asyncio import AsyncSession


class OpsService:
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
        if payload.approved and policy.executable:
            await OpsGovernanceBridge.resume_after_approval(
                session=session, user_id=user_id, run_id=run_id
            )
        action = await OpsRepository.create_action(
            incident_id, action=payload.action, target=incident.service,
            approved=payload.approved, reason=payload.reason,
        )
        if not payload.approved or not policy.executable:
            await OpsGovernanceBridge.event(
                session=session, user_id=user_id, run_id=run_id,
                event_type="ops.remediation_blocked", stage="ops.remediation",
                payload={"action": payload.action, "target": incident.service,
                         "approved": payload.approved, "policy_decision": policy.decision,
                         "policy_reason": policy.reason},
            )
            return await OpsRepository.finish_action(
                action.id, status='denied',
                error='Governance policy or human approval blocked the remediation.'
            )
        await OpsGovernanceBridge.event(
            session=session, user_id=user_id, run_id=run_id,
            event_type="ops.remediation_started", stage="ops.remediation",
            payload={"action": payload.action, "target": incident.service},
        )
        await OpsRepository.set_incident_status(incident_id, 'mitigating')
        try:
            result = await OpsAgentClient().restart(
                incident.service, approved=True, reason=payload.reason
            )
        except Exception as exc:
            failed = await OpsRepository.set_incident_status(incident_id, 'failed')
            await OpsGovernanceBridge.event(
                session=session, user_id=user_id, run_id=run_id,
                event_type="ops.recovery_failed", stage="ops.recovery",
                payload={"action": payload.action, "target": incident.service, "error": str(exc)},
            )
            await OpsGovernanceBridge.finish(
                session=session, user_id=user_id, run_id=run_id, incident=failed,
                success=False, action=payload.action, error=str(exc),
            )
            return await OpsRepository.finish_action(
                action.id, status='failed', error=str(exc)
            )

        finished = await OpsRepository.finish_action(
            action.id, status='completed', result=result
        )
        resolved = await OpsRepository.set_incident_status(incident_id, 'resolved')
        await OpsGovernanceBridge.event(
            session=session, user_id=user_id, run_id=run_id,
            event_type="ops.recovery_verified", stage="ops.recovery",
            payload={"action": payload.action, "target": incident.service, "result": result},
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
                payload={
                    "action": payload.action,
                    "target": incident.service,
                    "error": str(exc),
                    "recovery_verified": True,
                },
            )
            raise

        return finished

