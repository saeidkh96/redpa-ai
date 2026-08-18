from fastapi import APIRouter
from app.cloud_readiness_v15.schemas import CloudReadinessInput
from app.cloud_readiness_v15.engine import cloud_readiness_engine
router=APIRouter(prefix="/cloud-readiness/v15",tags=["V15"])
@router.post("/assess")
async def assess(payload:CloudReadinessInput):
    return cloud_readiness_engine.assess(payload)
