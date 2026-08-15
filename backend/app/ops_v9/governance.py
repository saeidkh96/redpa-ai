from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.governance_v10.schemas import AgentRunCreate, AgentRunEventCreate, AgentRunUpdate, RunEvaluationRequest, RunPolicyCheckRequest
from app.governance_v10.service import AgentGovernanceService
from app.models.evaluation import EvaluationMetric
from app.models.governance_v10 import AgentRunStatus
from app.ops_v9.schemas import IncidentRecord
from app.schemas.evaluation import EvaluationInput


class OpsGovernanceBridge:
    """V10 governance adapter for the V9 incident/remediation lifecycle."""

    @staticmethod
    async def start_incident_run(*, session: AsyncSession, user_id: uuid.UUID, incident: IncidentRecord):
        service = AgentGovernanceService()
        run = await service.create_run(
            session=session, user_id=user_id,
            payload=AgentRunCreate(
                agent_id="redpa-ops-agent", workflow_id=str(incident.id),
                objective=f"Diagnose and recover {incident.service}: {incident.summary}",
                input_payload={"incident_id": str(incident.id), "service": incident.service,
                               "severity": incident.severity, "source": incident.source},
                metadata={"integration": "v10_phase3", "domain": "operations_v9"},
            ),
        )
        return await service.update_run(
            session=session, run_id=run.id, user_id=user_id,
            payload=AgentRunUpdate(status=AgentRunStatus.RUNNING),
        )

    @staticmethod
    async def event(*, session: AsyncSession, user_id: uuid.UUID, run_id: uuid.UUID,
                    event_type: str, stage: str, payload: dict[str, Any] | None = None):
        return await AgentGovernanceService().add_event(
            session=session, run_id=run_id, user_id=user_id,
            payload=AgentRunEventCreate(event_type=event_type, stage=stage, payload=payload or {}),
        )

    @staticmethod
    async def resume_after_approval(*, session: AsyncSession, user_id: uuid.UUID, run_id: uuid.UUID):
        return await AgentGovernanceService().resume_run(
            session=session, run_id=run_id, user_id=user_id
        )

    @staticmethod
    async def remediation_policy(*, session: AsyncSession, user_id: uuid.UUID, run_id: uuid.UUID,
                                 incident: IncidentRecord, action: str, reason: str, approved: bool):
        return await AgentGovernanceService().policy_check(
            session=session, run_id=run_id, user_id=user_id,
            payload=RunPolicyCheckRequest(
                boundary="ops_remediation", action=action, resource=incident.service,
                arguments={"target": incident.service, "reason": reason},
                request_content=incident.summary, approval_granted=approved,
                metadata={"incident_id": str(incident.id), "severity": incident.severity},
            ),
        )

    @staticmethod
    async def finish(*, session: AsyncSession, user_id: uuid.UUID, run_id: uuid.UUID,
                     incident: IncidentRecord, success: bool, action: str | None = None,
                     error: str | None = None):
        service = AgentGovernanceService()
        status = AgentRunStatus.COMPLETED if success else AgentRunStatus.FAILED
        run = await service.update_run(
            session=session, run_id=run_id, user_id=user_id,
            payload=AgentRunUpdate(
                status=status,
                output_payload={"incident_id": str(incident.id), "incident_status": incident.status,
                                "service": incident.service, "action": action, "success": success},
                error=error,
            ),
        )
        if success:
            await service.evaluate_run(
                session=session, run_id=run_id, user_id=user_id,
                payload=RunEvaluationRequest(
                    metrics=[EvaluationMetric.TASK_SUCCESS],
                    input=EvaluationInput(
                        request_text=f"Recover incident {incident.id} for {incident.service}",
                        response_text=f"Incident status: {incident.status}", success=True,
                        actual_tools=[action] if action else [],
                        metadata={"incident_id": str(incident.id), "domain": "operations_v9"},
                    ),
                    evaluator_version="v10-phase3-ops",
                ),
            )
        return run
