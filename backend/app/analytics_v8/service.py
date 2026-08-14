from __future__ import annotations

from app.analytics_v8.repository import AnalyticsRepository
from app.analytics_v8.schemas import AnalyticsCatalog, AnalyticsEventBatch, KPIQueryRequest, KPIQueryResponse


class AnalyticsService:
    @staticmethod
    async def ingest(payload: AnalyticsEventBatch) -> int:
        return await AnalyticsRepository.insert_events(payload.items)

    @staticmethod
    async def catalog() -> AnalyticsCatalog:
        return await AnalyticsRepository.catalog()

    @staticmethod
    async def query(payload: KPIQueryRequest) -> KPIQueryResponse:
        return await AnalyticsRepository.query(payload)
