from __future__ import annotations

import os
import uuid

from app.database.session import AsyncSessionFactory
from app.governance_v10.repository import AgentRunRepository
from app.ops_v9.governance import OpsGovernanceBridge
from app.ops_v9.schemas import IncidentRecord, RemediationRequest
from app.ops_v9.service import OpsService


def configured_owner_user_id() -> uuid.UUID | None:
    raw = os.getenv("PRODUCTION_VALIDATION_OWNER_USER_ID", "").strip()
    if not raw:
        return None
    try:
        return uuid.UUID(raw)
    except ValueError as exc:
        raise RuntimeError("PRODUCTION_VALIDATION_OWNER_USER_ID must be a UUID") from exc


class ProductionRecoveryCoordinator:
    """Connect automatic incidents to the existing governed Ops lifecycle.

    It deliberately stops at the policy/approval boundary. A REVIEW decision is
    never auto-approved. The configured owner can resume the existing governed
    remediation endpoint with approved=true.
    """

    async def prepare_governed_recovery(self, incident: IncidentRecord):
        user_id = configured_owner_user_id()
        if user_id is None:
            return None

        async with AsyncSessionFactory() as session:
            existing = await AgentRunRepository.find_by_workflow(
                session=session, workflow_id=str(incident.id), user_id=user_id
            )
            if existing is not None:
                return existing

            run = await OpsGovernanceBridge.start_incident_run(
                session=session, user_id=user_id, incident=incident
            )
            diagnosed = await OpsService.diagnose_governed(
                incident.id, session=session, user_id=user_id, run_id=run.id
            )
            recommendation = diagnosed.diagnosis.get("recommendation")
            if recommendation != "restart_container":
                await OpsGovernanceBridge.event(
                    session=session, user_id=user_id, run_id=run.id,
                    event_type="ops.remediation_not_applicable",
                    stage="ops.remediation",
                    payload={"recommendation": recommendation},
                )
                return run

            await OpsService.remediate_governed(
                incident.id,
                RemediationRequest(
                    action="restart_container",
                    reason="Automatic production validation recovery candidate",
                    approved=False,
                ),
                session=session, user_id=user_id, run_id=run.id,
            )
            return await AgentRunRepository.get(
                session=session, run_id=run.id, user_id=user_id
            )


production_recovery_coordinator = ProductionRecoveryCoordinator()
