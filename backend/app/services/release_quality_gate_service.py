from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.benchmark import BenchmarkRunRecord
from app.models.release_quality_gate import ReleaseQualityGateRecord
from app.schemas.evaluation_regression import QualityGateRequest
from app.schemas.release_quality import (
    BenchmarkTrendPoint,
    BenchmarkTrendResponse,
    ReleaseQualityGateHistoryResponse,
    ReleaseQualityGateRequest,
    ReleaseQualityGateResponse,
)
from app.services.evaluation_regression_service import EvaluationRegressionService
from app.services.evaluation_service import EvaluationRunNotFoundError, EvaluationService


class ReleaseQualityGateService:
    def __init__(
        self,
        *,
        evaluation_service: EvaluationService | None = None,
        regression_service: EvaluationRegressionService | None = None,
    ) -> None:
        self.evaluation_service = evaluation_service or EvaluationService()
        self.regression_service = regression_service or EvaluationRegressionService()

    async def evaluate_and_persist(
        self,
        *,
        session: AsyncSession,
        request: ReleaseQualityGateRequest,
    ) -> ReleaseQualityGateResponse:
        baseline = await self.evaluation_service.get_by_id(
            session=session,
            run_id=request.baseline_run_id,
        )
        candidate = await self.evaluation_service.get_by_id(
            session=session,
            run_id=request.candidate_run_id,
        )

        gate_request = QualityGateRequest(
            baseline_run_id=request.baseline_run_id,
            candidate_run_id=request.candidate_run_id,
            max_aggregate_drop=request.max_aggregate_drop,
            max_metric_drop=request.max_metric_drop,
            require_candidate_pass=request.require_candidate_pass,
            minimum_candidate_score=request.minimum_candidate_score,
        )
        result = self.regression_service.quality_gate(
            baseline=baseline,
            candidate=candidate,
            request=gate_request,
        )

        record = ReleaseQualityGateRecord(
            baseline_run_id=request.baseline_run_id,
            candidate_run_id=request.candidate_run_id,
            release_label=request.release_label,
            decision=result.decision,
            reasons=list(result.reasons),
            baseline_score=result.regression.baseline_score,
            candidate_score=result.regression.candidate_score,
            aggregate_delta=result.regression.aggregate_delta,
            regression_detected=result.regression.regression_detected,
            regressed_metrics=list(result.regression.regressed_metrics),
            max_aggregate_drop=request.max_aggregate_drop,
            max_metric_drop=request.max_metric_drop,
            minimum_candidate_score=request.minimum_candidate_score,
            require_candidate_pass=request.require_candidate_pass,
            gate_metadata=dict(request.metadata),
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)

        return ReleaseQualityGateResponse(
            id=record.id,
            decision=result.decision,
            reasons=list(result.reasons),
            release_label=record.release_label,
            regression=result.regression,
            created_at=record.created_at,
        )

    async def history(
        self,
        *,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
        decision: str | None = None,
    ) -> ReleaseQualityGateHistoryResponse:
        filters = []
        if decision:
            filters.append(ReleaseQualityGateRecord.decision == decision.upper())

        result = await session.execute(
            select(ReleaseQualityGateRecord)
            .where(*filters)
            .order_by(ReleaseQualityGateRecord.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        count = await session.execute(
            select(func.count())
            .select_from(ReleaseQualityGateRecord)
            .where(*filters)
        )
        items = list(result.scalars().all())
        return ReleaseQualityGateHistoryResponse(
            items=items,
            total=int(count.scalar_one()),
            limit=limit,
            offset=offset,
        )

    @staticmethod
    async def benchmark_trend(
        *,
        session: AsyncSession,
        limit: int = 100,
        agent_id: str | None = None,
        model_name: str | None = None,
    ) -> BenchmarkTrendResponse:
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
        )
        items = list(reversed(list(result.scalars().all())))
        return BenchmarkTrendResponse(
            items=[
                BenchmarkTrendPoint(
                    id=item.id,
                    name=item.name,
                    agent_id=item.agent_id,
                    model_name=item.model_name,
                    aggregate_score=item.aggregate_score,
                    pass_rate=item.pass_rate,
                    metric_averages=item.metric_averages,
                    created_at=item.created_at,
                )
                for item in items
            ],
            total=len(items),
            agent_id=agent_id,
            model_name=model_name,
        )
