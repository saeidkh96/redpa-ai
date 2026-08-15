from __future__ import annotations
from uuid import UUID

from app.ops_v9.client import OpsAgentClient
from app.ops_v9.repository import OpsRepository
from app.ops_v9.schemas import RemediationRequest


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
