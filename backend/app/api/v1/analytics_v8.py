from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel

from app.analytics_v8.schemas import AnalyticsCatalog, AnalyticsEventBatch, KPIQueryRequest, KPIQueryResponse
from app.analytics_v8.service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["V8 Analytics & KPI"])


class IngestResponse(BaseModel):
    accepted: int


@router.post("/events", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_events(payload: AnalyticsEventBatch) -> IngestResponse:
    return IngestResponse(accepted=await AnalyticsService.ingest(payload))


@router.get("/catalog", response_model=AnalyticsCatalog)
async def analytics_catalog() -> AnalyticsCatalog:
    return await AnalyticsService.catalog()


@router.post("/query", response_model=KPIQueryResponse)
async def query_kpi(payload: KPIQueryRequest) -> KPIQueryResponse:
    return await AnalyticsService.query(payload)
