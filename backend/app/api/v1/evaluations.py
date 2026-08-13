from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import DatabaseSession
from app.evaluation.benchmark import (
    BenchmarkCase,
    BenchmarkEngine,
    BenchmarkRunResult,
)
from app.evaluation.telemetry import evaluation_telemetry
from app.models.evaluation import EvaluationRunStatus
from app.schemas.benchmark import (
    BenchmarkComparisonRequest,
    BenchmarkComparisonResponse,
    BenchmarkRunRequest,
    BenchmarkRunResponse,
)
from app.schemas.benchmark_persistence import (
    PersistedBenchmarkRunListResponse,
    PersistedBenchmarkRunResponse,
)
from app.schemas.evaluation import (
    EvaluationRequest,
    EvaluationRunListResponse,
    EvaluationRunResponse,
)
from app.schemas.evaluation_observability import (
    EvaluationObservabilityResponse,
)
from app.schemas.evaluation_regression import (
    EvaluationRegressionRequest,
    EvaluationRegressionResponse,
    QualityGateRequest,
    QualityGateResponse,
)
from app.services.benchmark_persistence_service import (
    BenchmarkPersistenceService,
    BenchmarkRunNotFoundError,
)
from app.services.evaluation_service import (
    EvaluationRunNotFoundError,
    EvaluationService,
)
from app.services.evaluation_regression_service import (
    EvaluationRegressionService,
)


router = APIRouter(
    prefix="/evaluations",
    tags=["Evaluations"],
)

service = EvaluationService()
benchmark_engine = BenchmarkEngine(
    evaluation_service=service,
)
regression_service = EvaluationRegressionService()
benchmark_store = BenchmarkPersistenceService()


@router.post(
    "",
    response_model=EvaluationRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and execute an evaluation run",
)
async def create_evaluation(
    request: EvaluationRequest,
    session: DatabaseSession,
) -> EvaluationRunResponse:
    run = await service.create_and_evaluate(
        session=session,
        request=request,
    )
    return EvaluationRunResponse.model_validate(run)


@router.get(
    "",
    response_model=EvaluationRunListResponse,
    status_code=status.HTTP_200_OK,
    summary="List evaluation runs",
)
async def list_evaluations(
    session: DatabaseSession,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    run_status: EvaluationRunStatus | None = Query(default=None, alias="status"),
    agent_id: str | None = Query(default=None, max_length=150),
) -> EvaluationRunListResponse:
    items, total = await service.get_all(
        session=session,
        limit=limit,
        offset=offset,
        status=run_status,
        agent_id=agent_id,
    )

    return EvaluationRunListResponse(
        items=[
            EvaluationRunResponse.model_validate(item)
            for item in items
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/metrics",
    response_model=list[str],
    status_code=status.HTTP_200_OK,
    summary="List supported evaluation metrics",
)
async def list_metrics() -> list[str]:
    return [
        metric.value
        for metric in service.registry.supported_metrics()
    ]


@router.get(
    "/observability",
    response_model=EvaluationObservabilityResponse,
    status_code=status.HTTP_200_OK,
    summary="Get evaluation and benchmark telemetry snapshot",
)
async def get_evaluation_observability() -> EvaluationObservabilityResponse:
    return EvaluationObservabilityResponse.model_validate(
        evaluation_telemetry.snapshot(),
    )


@router.get(
    "/benchmark-history",
    response_model=PersistedBenchmarkRunListResponse,
    status_code=status.HTTP_200_OK,
    summary="List persisted benchmark runs",
)
async def list_persisted_benchmarks(
    session: DatabaseSession,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    agent_id: str | None = Query(default=None, max_length=150),
    model_name: str | None = Query(default=None, max_length=200),
) -> PersistedBenchmarkRunListResponse:
    items, total = await benchmark_store.list(
        session=session,
        limit=limit,
        offset=offset,
        agent_id=agent_id,
        model_name=model_name,
    )
    return PersistedBenchmarkRunListResponse(
        items=[PersistedBenchmarkRunResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/benchmark-history/{run_id}",
    response_model=PersistedBenchmarkRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a persisted benchmark run",
)
async def get_persisted_benchmark(
    run_id: uuid.UUID,
    session: DatabaseSession,
) -> PersistedBenchmarkRunResponse:
    try:
        item = await benchmark_store.get(session=session, run_id=run_id)
    except BenchmarkRunNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return PersistedBenchmarkRunResponse.model_validate(item)


@router.get(
    "/{run_id}",
    response_model=EvaluationRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Get one evaluation run",
)
async def get_evaluation(
    run_id: uuid.UUID,
    session: DatabaseSession,
) -> EvaluationRunResponse:
    try:
        run = await service.get_by_id(
            session=session,
            run_id=run_id,
        )
    except EvaluationRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return EvaluationRunResponse.model_validate(run)


@router.post(
    "/benchmarks/run",
    response_model=BenchmarkRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Run an in-memory benchmark suite",
)
async def run_benchmark(
    request: BenchmarkRunRequest,
    session: DatabaseSession,
) -> BenchmarkRunResponse:
    cases = [
        BenchmarkCase(
            id=item.id,
            name=item.name,
            input=item.input,
            metrics=item.metrics,
            tags=item.tags,
            weights=item.weights,
            metadata=item.metadata,
        )
        for item in request.cases
    ]

    result = benchmark_engine.run(
        name=request.name,
        cases=cases,
        agent_id=request.agent_id,
        model_name=request.model_name,
        pass_threshold=request.pass_threshold,
    )

    await benchmark_store.save(
        session=session,
        result=result,
        pass_threshold=request.pass_threshold,
    )

    return BenchmarkRunResponse.model_validate(
        {
            "id": result.id,
            "name": result.name,
            "agent_id": result.agent_id,
            "model_name": result.model_name,
            "created_at": result.created_at,
            "case_results": result.case_results,
            "aggregate_score": result.aggregate_score,
            "pass_rate": result.pass_rate,
            "metric_averages": result.metric_averages,
        },
    )


@router.post(
    "/benchmarks/compare",
    response_model=BenchmarkComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare benchmark runs",
)
async def compare_benchmarks(
    request: BenchmarkComparisonRequest,
) -> BenchmarkComparisonResponse:
    runs = [
        BenchmarkRunResult(
            id=item.id,
            name=item.name,
            agent_id=item.agent_id,
            model_name=item.model_name,
            created_at=item.created_at,
            case_results=[],
            aggregate_score=item.aggregate_score,
            pass_rate=item.pass_rate,
            metric_averages=item.metric_averages,
        )
        for item in request.runs
    ]

    return BenchmarkComparisonResponse(
        items=benchmark_engine.compare(runs),
    )


@router.post(
    "/regression/compare",
    response_model=EvaluationRegressionResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare a persisted candidate evaluation against a persisted baseline",
)
async def compare_evaluation_regression(
    request: EvaluationRegressionRequest,
    session: DatabaseSession,
) -> EvaluationRegressionResponse:
    try:
        baseline = await service.get_by_id(
            session=session,
            run_id=request.baseline_run_id,
        )
        candidate = await service.get_by_id(
            session=session,
            run_id=request.candidate_run_id,
        )
    except EvaluationRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return regression_service.compare(
        baseline=baseline,
        candidate=candidate,
        request=request,
    )


@router.post(
    "/quality-gates/evaluate",
    response_model=QualityGateResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate a persisted candidate evaluation against regression quality gates",
)
async def evaluate_quality_gate(
    request: QualityGateRequest,
    session: DatabaseSession,
) -> QualityGateResponse:
    try:
        baseline = await service.get_by_id(
            session=session,
            run_id=request.baseline_run_id,
        )
        candidate = await service.get_by_id(
            session=session,
            run_id=request.candidate_run_id,
        )
    except EvaluationRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return regression_service.quality_gate(
        baseline=baseline,
        candidate=candidate,
        request=request,
    )
