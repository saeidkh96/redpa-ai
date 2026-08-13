from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.models.release_quality_gate import ReleaseQualityGateRecord
from app.schemas.release_quality import ReleaseQualityGateRequest
from app.services.release_quality_gate_service import ReleaseQualityGateService


def make_run(score: float, threshold: float, metrics: dict[str, float]):
    return SimpleNamespace(
        id=uuid.uuid4(),
        aggregate_score=score,
        pass_threshold=threshold,
        results=[SimpleNamespace(metric=name, score=value) for name, value in metrics.items()],
    )


class FakeEvaluationService:
    def __init__(self, baseline, candidate):
        self.baseline = baseline
        self.candidate = candidate

    async def get_by_id(self, *, session, run_id):
        del session
        if run_id == self.baseline.id:
            return self.baseline
        if run_id == self.candidate.id:
            return self.candidate
        raise AssertionError("unexpected run id")


class FakeSession:
    def __init__(self):
        self.added = []

    def add(self, item):
        self.added.append(item)

    async def commit(self):
        return None

    async def refresh(self, item):
        if item.id is None:
            item.id = uuid.uuid4()
        if item.created_at is None:
            item.created_at = datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_release_gate_persists_pass_decision():
    baseline = make_run(0.80, 0.70, {"task_success": 0.80})
    candidate = make_run(0.86, 0.70, {"task_success": 0.86})
    session = FakeSession()
    service = ReleaseQualityGateService(
        evaluation_service=FakeEvaluationService(baseline, candidate),
    )

    result = await service.evaluate_and_persist(
        session=session,
        request=ReleaseQualityGateRequest(
            baseline_run_id=baseline.id,
            candidate_run_id=candidate.id,
            release_label="v5.5-candidate",
            minimum_candidate_score=0.75,
        ),
    )

    assert result.decision == "PASS"
    assert result.release_label == "v5.5-candidate"
    assert len(session.added) == 1
    assert session.added[0].decision == "PASS"


@pytest.mark.asyncio
async def test_release_gate_persists_fail_decision():
    baseline = make_run(0.90, 0.70, {"task_success": 0.90, "latency": 0.90})
    candidate = make_run(0.60, 0.70, {"task_success": 0.60, "latency": 0.60})
    session = FakeSession()
    service = ReleaseQualityGateService(
        evaluation_service=FakeEvaluationService(baseline, candidate),
    )

    result = await service.evaluate_and_persist(
        session=session,
        request=ReleaseQualityGateRequest(
            baseline_run_id=baseline.id,
            candidate_run_id=candidate.id,
            max_aggregate_drop=0.05,
            max_metric_drop=0.10,
            minimum_candidate_score=0.70,
        ),
    )

    assert result.decision == "FAIL"
    assert result.regression.regression_detected is True
    assert session.added[0].regression_detected is True


def test_release_quality_gate_model_contract():
    assert ReleaseQualityGateRecord.__tablename__ == "release_quality_gates"
    columns = {column.name for column in ReleaseQualityGateRecord.__table__.columns}
    assert {
        "id",
        "baseline_run_id",
        "candidate_run_id",
        "release_label",
        "decision",
        "reasons",
        "baseline_score",
        "candidate_score",
        "aggregate_delta",
        "regression_detected",
        "regressed_metrics",
        "metadata",
        "created_at",
    }.issubset(columns)
