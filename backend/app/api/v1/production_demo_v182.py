from fastapi import APIRouter

from app.production_demo_v182.schemas import ProductionDemoRequest, ProductionDemoResult
from app.production_demo_v182.service import production_demo_service

router = APIRouter(prefix="/production-demo/v18.2", tags=["V18.2 Production E2E Demo"])


@router.post("/run", response_model=ProductionDemoResult)
async def run_demo(payload: ProductionDemoRequest) -> ProductionDemoResult:
    return await production_demo_service.run(payload)
