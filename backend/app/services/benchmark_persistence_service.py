from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.evaluation.benchmark import BenchmarkRunResult
from app.models.benchmark import BenchmarkRunRecord


class BenchmarkRunNotFoundError(Exception):
    pass


class BenchmarkPersistenceService:
    @staticmethod
    async def save(
        *,
        session: AsyncSession,
        result: BenchmarkRunResult,
        pass_threshold: float,
    ) -> BenchmarkRunRecord:
        record = BenchmarkRunRecord(
            id=uuid.UUID(result.id),
            name=result.name,
            agent_id=result.agent_id,
            model_name=result.model_name,
            aggregate_score=result.aggregate_score,
            pass_rate=result.pass_rate,
            pass_threshold=pass_threshold,
            metric_averages=dict(result.metric_averages),
            case_results=[
                {
                    "case_id": item.case_id,
                    "case_name": item.case_name,
                    "aggregate_score": item.aggregate_score,
                    "metric_scores": dict(item.metric_scores),
                    "passed": item.passed,
                    "tags": list(item.tags),
                    "metadata": dict(item.metadata),
                }
                for item in result.case_results
            ],
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return record

    @staticmethod
    async def list(
        *,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
        agent_id: str | None = None,
        model_name: str | None = None,
    ) -> tuple[list[BenchmarkRunRecord], int]:
        filters = []
        if agent_id:
            filters.append(BenchmarkRunRecord.agent_id == agent_id)
        if model_name:
            filters.append(BenchmarkRunRecord.model_name == model_name)

        result = await session.execute(
            select(BenchmarkRunRecord)
            .where(*filters)
            .order_by(BenchmarkRunRecord.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        count = await session.execute(
            select(func.count()).select_from(BenchmarkRunRecord).where(*filters)
        )
        return list(result.scalars().all()), int(count.scalar_one())

    @staticmethod
    async def get(
        *,
        session: AsyncSession,
        run_id: uuid.UUID,
    ) -> BenchmarkRunRecord:
        record = await session.get(BenchmarkRunRecord, run_id)
        if record is None:
            raise BenchmarkRunNotFoundError("Benchmark run not found.")
        return record
