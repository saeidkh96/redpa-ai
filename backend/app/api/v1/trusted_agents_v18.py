from fastapi import APIRouter
from app.trusted_agents_v18.schemas import TrustedAgentInput
from app.trusted_agents_v18.engine import trusted_agent_engine
router=APIRouter(prefix="/trusted-agents/v18",tags=["V18"])
@router.post("/assess")
async def assess(payload:TrustedAgentInput):
    return trusted_agent_engine.evaluate(payload)
