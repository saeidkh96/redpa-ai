from __future__ import annotations

import uuid
from typing import Iterable

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.evaluation.metrics import EvaluationMetricRegistry
from app.evaluation.telemetry import evaluation_telemetry
from app.models.evaluation import (
    EvaluationResult,
    EvaluationRun,
    EvaluationRunStatus,
)
from app.schemas.evaluation import EvaluationRequest, MetricEvaluation


class EvaluationRunNotFoundError(Exception):
    """Raised when an evaluation run cannot be found."""


class EvaluationService:
    def __init__(
        self,
        *,
        registry: EvaluationMetricRegistry | None = None,
    ) -> None:
        self.registry = registry or EvaluationMetricRegistry()

    async def create_and_evaluate(
        self,
        *,
        session: AsyncSession,
        request: EvaluationRequest,
    ) -> EvaluationRun:
        run = await self.create_run(
            session=session,
            request=request,
            commit=False,
        )

        evaluation_telemetry.run_started()

        try:
            run.mark_running()

            metric_results = self.evaluate_metrics(
                request=request,
            )

            persisted_results = [
                EvaluationResult(
                    run_id=run.id,
                    metric=item.metric.value,
                    score=item.score,
                    passed=item.passed,
                    weight=item.weight,
                    details=item.details,
                    error=item.error,
                )
                for item in metric_results
            ]

            session.add_all(persisted_results)

            aggregate_score = self.aggregate_score(
                metric_results,
            )
            run.mark_completed(aggregate_score)

            await session.commit()

            evaluation_telemetry.run_completed(
                aggregate_score,
            )

        except Exception as exc:
            await session.rollback()
            evaluation_telemetry.run_failed()

            failed_run = await session.get(
                EvaluationRun,
                run.id,
            )
            if failed_run is not None:
                failed_run.mark_failed(str(exc))
                await session.commit()

            raise

        return await self.get_by_id(
            session=session,
            run_id=run.id,
        )

    async def create_run(
        self,
        *,
        session: AsyncSession,
        request: EvaluationRequest,
        commit: bool = True,
    ) -> EvaluationRun:
        run = EvaluationRun(
            name=request.name,
            status=EvaluationRunStatus.PENDING.value,
            evaluator_version=request.evaluator_version,
            source_type=request.source_type,
            source_id=request.source_id,
            agent_id=request.agent_id,
            model_name=request.model_name,
            pass_threshold=request.pass_threshold,
            metadata_=request.metadata or None,
        )

        session.add(run)

        if commit:
            await session.commit()
            await session.refresh(run)
        else:
            await session.flush()

        return run

    def evaluate_metrics(
        self,
        *,
        request: EvaluationRequest,
    ) -> list[MetricEvaluation]:
        results: list[MetricEvaluation] = []

        for metric in request.metrics:
            weight = request.weights.get(metric, 1.0)

            try:
                metric_result = self.registry.evaluate(
                    metric=metric,
                    evaluation_input=request.input,
                )

                item = MetricEvaluation(
                    metric=metric,
                    score=metric_result.score,
                    passed=(
                        metric_result.score
                        >= request.pass_threshold
                    ),
                    weight=weight,
                    details=metric_result.details,
                )
            except Exception as exc:
                item = MetricEvaluation(
                    metric=metric,
                    score=0.0,
                    passed=False,
                    weight=weight,
                    details={},
                    error=str(exc),
                )

            evaluation_telemetry.metric_recorded(
                metric=item.metric.value,
                score=item.score,
                passed=item.passed,
            )
            results.append(item)

        return results

    @staticmethod
    def aggregate_score(
        results: Iterable[MetricEvaluation],
    ) -> float:
        result_list = list(results)

        if not result_list:
            return 0.0

        total_weight = sum(
            item.weight
            for item in result_list
        )

        if total_weight <= 0:
            return 0.0

        weighted_score = sum(
            item.score * item.weight
            for item in result_list
        )

        return max(
            0.0,
            min(
                1.0,
                weighted_score / total_weight,
            ),
        )

    async def get_by_id(
        self,
        *,
        session: AsyncSession,
        run_id: uuid.UUID,
    ) -> EvaluationRun:
        statement = (
            select(EvaluationRun)
            .where(
                EvaluationRun.id == run_id,
            )
            .options(
                selectinload(
                    EvaluationRun.results,
                ),
            )
        )

        result = await session.execute(statement)
        run = result.scalar_one_or_none()

        if run is None:
            raise EvaluationRunNotFoundError(
                "Evaluation run not found.",
            )

        return run

    async def get_all(
        self,
        *,
        session: AsyncSession,
        limit: int,
        offset: int,
        status: EvaluationRunStatus | None = None,
        agent_id: str | None = None,
    ) -> tuple[list[EvaluationRun], int]:
        filters = []

        if status is not None:
            filters.append(
                EvaluationRun.status == status.value,
            )

        if agent_id:
            filters.append(
                EvaluationRun.agent_id == agent_id,
            )

        statement = (
            select(EvaluationRun)
            .where(*filters)
            .options(
                selectinload(
                    EvaluationRun.results,
                ),
            )
            .order_by(
                EvaluationRun.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        count_statement = (
            select(func.count())
            .select_from(EvaluationRun)
            .where(*filters)
        )

        result = await session.execute(statement)
        count_result = await session.execute(count_statement)

        return (
            list(result.scalars().unique().all()),
            count_result.scalar_one(),
        )
