from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.evaluation.benchmark import BenchmarkCase, BenchmarkEngine
from app.models.benchmark import BenchmarkRunRecord
from app.models.evaluation import EvaluationRun
from app.models.quality_registry import BenchmarkSuiteRecord, ReliabilitySnapshotRecord
from app.models.release_quality_gate import ReleaseQualityGateRecord
from app.schemas.benchmark import BenchmarkCaseRequest, BenchmarkRunResponse
from app.schemas.quality_registry import (
    BenchmarkSuiteCreateRequest,
    BenchmarkSuiteListResponse,
    BenchmarkSuiteResponse,
    BenchmarkSuiteRunRequest,
    BenchmarkSuiteRunResponse,
    ReliabilityCaptureResponse,
    ReliabilityHistoryResponse,
    ReliabilitySnapshotResponse,
    ReleaseCandidateReportResponse,
)
from app.schemas.reliability_validation import ReliabilityScorecardResponse
from app.services.benchmark_persistence_service import BenchmarkPersistenceService


class BenchmarkSuiteNotFoundError(Exception):
    pass


class QualityRegistryService:
    def __init__(self) -> None:
        self.benchmark_engine = BenchmarkEngine()
        self.benchmark_store = BenchmarkPersistenceService()

    async def create_suite(
        self,
        *,
        session: AsyncSession,
        request: BenchmarkSuiteCreateRequest,
    ) -> BenchmarkSuiteResponse:
        record = BenchmarkSuiteRecord(
            name=request.name,
            description=request.description,
            cases=[case.model_dump(mode="json") for case in request.cases],
            pass_threshold=request.pass_threshold,
            enabled=request.enabled,
            suite_metadata=dict(request.metadata),
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return BenchmarkSuiteResponse.model_validate(record)

    @staticmethod
    async def list_suites(
        *,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
        enabled: bool | None = None,
    ) -> BenchmarkSuiteListResponse:
        filters = []
        if enabled is not None:
            filters.append(BenchmarkSuiteRecord.enabled == enabled)

        result = await session.execute(
            select(BenchmarkSuiteRecord)
            .where(*filters)
            .order_by(BenchmarkSuiteRecord.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        count = await session.execute(
            select(func.count()).select_from(BenchmarkSuiteRecord).where(*filters)
        )
        return BenchmarkSuiteListResponse(
            items=list(result.scalars().all()),
            total=int(count.scalar_one()),
            limit=limit,
            offset=offset,
        )

    @staticmethod
    async def get_suite(
        *,
        session: AsyncSession,
        suite_id: uuid.UUID,
    ) -> BenchmarkSuiteRecord:
        record = await session.get(BenchmarkSuiteRecord, suite_id)
        if record is None:
            raise BenchmarkSuiteNotFoundError("Benchmark suite not found.")
        return record

    async def run_suite(
        self,
        *,
        session: AsyncSession,
        suite_id: uuid.UUID,
        request: BenchmarkSuiteRunRequest,
    ) -> BenchmarkSuiteRunResponse:
        suite = await self.get_suite(session=session, suite_id=suite_id)
        if not suite.enabled:
            raise ValueError("Benchmark suite is disabled.")

        parsed_cases = [BenchmarkCaseRequest.model_validate(item) for item in suite.cases]
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
            for item in parsed_cases
        ]
        result = self.benchmark_engine.run(
            name=request.run_name or f"{suite.name} run",
            cases=cases,
            agent_id=request.agent_id,
            model_name=request.model_name,
            pass_threshold=suite.pass_threshold,
        )
        await self.benchmark_store.save(
            session=session,
            result=result,
            pass_threshold=suite.pass_threshold,
        )
        return BenchmarkSuiteRunResponse(
            suite_id=suite.id,
            benchmark=BenchmarkRunResponse.model_validate({
                "id": result.id,
                "name": result.name,
                "agent_id": result.agent_id,
                "model_name": result.model_name,
                "created_at": result.created_at,
                "case_results": [
                    {
                        "case_id": item.case_id,
                        "case_name": item.case_name,
                        "aggregate_score": item.aggregate_score,
                        "metric_scores": item.metric_scores,
                        "passed": item.passed,
                        "tags": item.tags,
                        "metadata": item.metadata,
                    }
                    for item in result.case_results
                ],
                "aggregate_score": result.aggregate_score,
                "pass_rate": result.pass_rate,
                "metric_averages": result.metric_averages,
            }),
        )

    @staticmethod
    async def capture_reliability(
        *,
        session: AsyncSession,
        scorecard: ReliabilityScorecardResponse,
    ) -> ReliabilityCaptureResponse:
        record = ReliabilitySnapshotRecord(
            overall_score=scorecard.overall_score,
            healthy_providers=scorecard.healthy_providers,
            degraded_providers=scorecard.degraded_providers,
            unavailable_providers=scorecard.unavailable_providers,
            providers=[item.model_dump(mode="json") for item in scorecard.providers],
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return ReliabilityCaptureResponse(
            snapshot=ReliabilitySnapshotResponse.model_validate(record),
            scorecard=scorecard,
        )

    @staticmethod
    async def reliability_history(
        *,
        session: AsyncSession,
        limit: int = 100,
        offset: int = 0,
    ) -> ReliabilityHistoryResponse:
        result = await session.execute(
            select(ReliabilitySnapshotRecord)
            .order_by(ReliabilitySnapshotRecord.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        count = await session.execute(
            select(func.count()).select_from(ReliabilitySnapshotRecord)
        )
        return ReliabilityHistoryResponse(
            items=list(result.scalars().all()),
            total=int(count.scalar_one()),
            limit=limit,
            offset=offset,
        )

    @staticmethod
    async def release_candidate_report(
        *,
        session: AsyncSession,
        candidate_run_id: uuid.UUID,
    ) -> ReleaseCandidateReportResponse:
        candidate = await session.get(EvaluationRun, candidate_run_id)
        if candidate is None:
            raise ValueError("Candidate evaluation run not found.")

        gate_result = await session.execute(
            select(ReleaseQualityGateRecord)
            .where(ReleaseQualityGateRecord.candidate_run_id == candidate_run_id)
            .order_by(ReleaseQualityGateRecord.created_at.desc())
            .limit(1)
        )
        gate = gate_result.scalar_one_or_none()

        benchmark = None
        benchmark_filters = []
        if candidate.agent_id:
            benchmark_filters.append(BenchmarkRunRecord.agent_id == candidate.agent_id)
        if candidate.model_name:
            benchmark_filters.append(BenchmarkRunRecord.model_name == candidate.model_name)
        if benchmark_filters:
            benchmark_result = await session.execute(
                select(BenchmarkRunRecord)
                .where(*benchmark_filters)
                .order_by(BenchmarkRunRecord.created_at.desc())
                .limit(1)
            )
            benchmark = benchmark_result.scalar_one_or_none()

        reliability_result = await session.execute(
            select(ReliabilitySnapshotRecord)
            .order_by(ReliabilitySnapshotRecord.created_at.desc())
            .limit(1)
        )
        reliability = reliability_result.scalar_one_or_none()

        blockers: list[str] = []
        candidate_score = float(candidate.aggregate_score or 0.0)
        if candidate_score < float(candidate.pass_threshold):
            blockers.append("candidate_below_run_pass_threshold")
        if gate is None:
            blockers.append("release_quality_gate_missing")
        elif gate.decision != "PASS":
            blockers.append("release_quality_gate_failed")
        if reliability is None:
            blockers.append("reliability_snapshot_missing")
        elif reliability.unavailable_providers > 0:
            blockers.append("provider_unavailable")

        return ReleaseCandidateReportResponse(
            candidate_run_id=candidate.id,
            candidate_name=candidate.name,
            candidate_score=candidate_score,
            candidate_threshold=float(candidate.pass_threshold),
            latest_gate_id=gate.id if gate else None,
            latest_gate_decision=gate.decision if gate else None,
            latest_gate_reasons=list(gate.reasons) if gate else [],
            latest_gate_created_at=gate.created_at if gate else None,
            latest_benchmark_id=benchmark.id if benchmark else None,
            latest_benchmark_score=benchmark.aggregate_score if benchmark else None,
            latest_benchmark_pass_rate=benchmark.pass_rate if benchmark else None,
            reliability_score=reliability.overall_score if reliability else None,
            reliability_snapshot_at=reliability.created_at if reliability else None,
            promotion_ready=not blockers,
            blockers=blockers,
        )
