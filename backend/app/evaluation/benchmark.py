from __future__ import annotations

import statistics
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

from app.evaluation.telemetry import evaluation_telemetry
from app.models.evaluation import EvaluationMetric
from app.schemas.evaluation import EvaluationInput, EvaluationRequest
from app.services.evaluation_service import EvaluationService


@dataclass(slots=True)
class BenchmarkCase:
    id: str
    name: str
    input: EvaluationInput
    metrics: list[EvaluationMetric]
    tags: list[str] = field(default_factory=list)
    weights: dict[EvaluationMetric, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BenchmarkCaseResult:
    case_id: str
    case_name: str
    aggregate_score: float
    metric_scores: dict[str, float]
    passed: bool
    tags: list[str]
    metadata: dict[str, Any]


@dataclass(slots=True)
class BenchmarkRunResult:
    id: str
    name: str
    agent_id: str | None
    model_name: str | None
    created_at: datetime
    case_results: list[BenchmarkCaseResult]
    aggregate_score: float
    pass_rate: float
    metric_averages: dict[str, float]


class BenchmarkEngine:
    def __init__(
        self,
        *,
        evaluation_service: EvaluationService | None = None,
    ) -> None:
        self.evaluation_service = evaluation_service or EvaluationService()

    def evaluate_case(
        self,
        *,
        case: BenchmarkCase,
        pass_threshold: float = 0.70,
    ) -> BenchmarkCaseResult:
        request = EvaluationRequest(
            name=case.name,
            metrics=case.metrics,
            input=case.input,
            weights=case.weights,
            pass_threshold=pass_threshold,
            metadata=case.metadata,
        )

        metric_results = self.evaluation_service.evaluate_metrics(
            request=request,
        )
        aggregate_score = self.evaluation_service.aggregate_score(
            metric_results,
        )

        return BenchmarkCaseResult(
            case_id=case.id,
            case_name=case.name,
            aggregate_score=aggregate_score,
            metric_scores={
                item.metric.value: item.score
                for item in metric_results
            },
            passed=aggregate_score >= pass_threshold,
            tags=list(case.tags),
            metadata=dict(case.metadata),
        )

    def run(
        self,
        *,
        name: str,
        cases: Iterable[BenchmarkCase],
        agent_id: str | None = None,
        model_name: str | None = None,
        pass_threshold: float = 0.70,
    ) -> BenchmarkRunResult:
        case_results = [
            self.evaluate_case(
                case=case,
                pass_threshold=pass_threshold,
            )
            for case in cases
        ]

        if not case_results:
            aggregate_score = 0.0
            pass_rate = 0.0
            metric_averages: dict[str, float] = {}
        else:
            aggregate_score = statistics.fmean(
                result.aggregate_score
                for result in case_results
            )
            pass_rate = (
                sum(1 for result in case_results if result.passed)
                / len(case_results)
            )

            metric_names = sorted({
                metric
                for result in case_results
                for metric in result.metric_scores
            })

            metric_averages = {}
            for metric_name in metric_names:
                values = [
                    result.metric_scores[metric_name]
                    for result in case_results
                    if metric_name in result.metric_scores
                ]
                metric_averages[metric_name] = (
                    statistics.fmean(values)
                    if values
                    else 0.0
                )

        evaluation_telemetry.benchmark_completed(
            aggregate_score=aggregate_score,
            case_passes=[
                result.passed
                for result in case_results
            ],
        )

        return BenchmarkRunResult(
            id=str(uuid.uuid4()),
            name=name,
            agent_id=agent_id,
            model_name=model_name,
            created_at=datetime.now(timezone.utc),
            case_results=case_results,
            aggregate_score=aggregate_score,
            pass_rate=pass_rate,
            metric_averages=metric_averages,
        )

    @staticmethod
    def compare(
        runs: Iterable[BenchmarkRunResult],
    ) -> list[dict[str, Any]]:
        ranked = sorted(
            list(runs),
            key=lambda item: (
                item.aggregate_score,
                item.pass_rate,
            ),
            reverse=True,
        )

        return [
            {
                "rank": index + 1,
                "benchmark_run_id": item.id,
                "name": item.name,
                "agent_id": item.agent_id,
                "model_name": item.model_name,
                "aggregate_score": item.aggregate_score,
                "pass_rate": item.pass_rate,
                "metric_averages": item.metric_averages,
            }
            for index, item in enumerate(ranked)
        ]
