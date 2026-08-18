from fastapi import APIRouter
from app.enterprise_integration_v17.schemas import ConnectorRiskInput
from app.enterprise_integration_v17.engine import connector_risk_engine
router=APIRouter(prefix="/enterprise-integration/v17",tags=["V17"])
@router.post("/assess")
async def assess(payload:ConnectorRiskInput):
    return connector_risk_engine.assess(payload)
