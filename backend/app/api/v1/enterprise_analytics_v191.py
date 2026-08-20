from fastapi import APIRouter

from app.api.dependencies import CurrentUser, DatabaseSession
from app.enterprise_analytics_v191.service import (
    governance_analytics_service,
)


router = APIRouter(
    prefix="/analytics/v19.1",
    tags=["V19.1 Governance Analytics"],
)


@router.get("/kpis")
async def governance_kpis(
    current_user: CurrentUser,
    session: DatabaseSession,
):
    return await governance_analytics_service.summary(
        session=session,
        user_id=current_user.id,
    )


@router.get("/evidence")
async def governance_evidence(
    current_user: CurrentUser,
    session: DatabaseSession,
):
    return await governance_analytics_service.evidence(
        session=session,
        user_id=current_user.id,
    )


@router.get("/capabilities")
async def analytics_capabilities(
    current_user: CurrentUser,
):
    return {
        "version": "19.1.0",
        "persisted_governance_metrics": True,
        "agent_run_metrics": True,
        "approval_metrics": True,
        "decision_latency": True,
        "governance_event_metrics": True,
        "audit_evidence_export": True,
        "live_power_bi_connection": False,
    }
