from fastapi import APIRouter

from app.reliability_v8.slo import SLOEvaluateRequest, SLOEvaluation, SLOEvaluator

router = APIRouter(prefix="/operations", tags=["V8 Operations & SLO"])


@router.post("/slo/evaluate", response_model=SLOEvaluation)
async def evaluate_slo(payload: SLOEvaluateRequest) -> SLOEvaluation:
    return SLOEvaluator.evaluate(payload)
