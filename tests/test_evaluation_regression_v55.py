from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from app.schemas.evaluation_regression import (
    EvaluationRegressionRequest,
    QualityGateRequest,
)
from app.services.evaluation_regression_service import (
    EvaluationRegressionService,
)


def make_run(score: float, threshold: float, metrics: dict[str, float]):
    return SimpleNamespace(
        id=uuid.uuid4(),
        aggregate_score=score,
        pass_threshold=threshold,
        results=[
            SimpleNamespace(metric=name, score=value)
            for name, value in metrics.items()
        ],
    )


def test_regression_detects_aggregate_and_metric_drop():
    baseline = make_run(
        0.90,
        0.70,
        {"task_success": 0.95, "latency": 0.90},
    )
    candidate = make_run(
        0.78,
        0.70,
        {"task_success": 0.80, "latency": 0.89},
    )

    result = EvaluationRegressionService.compare(
        baseline=baseline,
        candidate=candidate,
        request=EvaluationRegressionRequest(
            baseline_run_id=baseline.id,
            candidate_run_id=candidate.id,
            max_aggregate_drop=0.05,
            max_metric_drop=0.10,
        ),
    )

    assert result.regression_detected is True
    assert result.aggregate_delta == pytest.approx(-0.12)
    assert "task_success" in result.regressed_metrics


def test_quality_gate_passes_with_non_regressing_candidate():
    baseline = make_run(
        0.82,
        0.70,
        {"task_success": 0.80, "latency": 0.84},
    )
    candidate = make_run(
        0.86,
        0.70,
        {"task_success": 0.88, "latency": 0.84},
    )

    result = EvaluationRegressionService.quality_gate(
        baseline=baseline,
        candidate=candidate,
        request=QualityGateRequest(
            baseline_run_id=baseline.id,
            candidate_run_id=candidate.id,
            minimum_candidate_score=0.80,
        ),
    )

    assert result.decision == "PASS"
    assert result.reasons == ["quality_gate_passed"]


def test_quality_gate_fails_below_candidate_threshold():
    baseline = make_run(
        0.75,
        0.70,
        {"task_success": 0.75},
    )
    candidate = make_run(
        0.65,
        0.70,
        {"task_success": 0.65},
    )

    result = EvaluationRegressionService.quality_gate(
        baseline=baseline,
        candidate=candidate,
        request=QualityGateRequest(
            baseline_run_id=baseline.id,
            candidate_run_id=candidate.id,
            max_aggregate_drop=0.20,
            max_metric_drop=0.20,
            require_candidate_pass=True,
        ),
    )

    assert result.decision == "FAIL"
    assert "candidate_below_run_pass_threshold" in result.reasons


def test_missing_candidate_metric_is_regression():
    baseline = make_run(
        0.85,
        0.70,
        {"task_success": 0.90, "cost": 0.80},
    )
    candidate = make_run(
        0.85,
        0.70,
        {"task_success": 0.90},
    )

    result = EvaluationRegressionService.compare(
        baseline=baseline,
        candidate=candidate,
        request=EvaluationRegressionRequest(
            baseline_run_id=baseline.id,
            candidate_run_id=candidate.id,
        ),
    )

    assert result.regression_detected is True
    assert "cost" in result.regressed_metrics
