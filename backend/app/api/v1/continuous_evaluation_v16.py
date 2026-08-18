from fastapi import APIRouter
from app.continuous_evaluation_v16.schemas import EvaluationInput
from app.continuous_evaluation_v16.engine import continuous_evaluation_engine
router=APIRouter(prefix="/continuous-evaluation/v16",tags=["V16"])
@router.post("/assess")
async def assess(payload:EvaluationInput):
    return continuous_evaluation_engine.decide(payload)
