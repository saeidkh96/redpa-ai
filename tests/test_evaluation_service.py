import pytest
from pydantic import ValidationError

from app.models.evaluation import EvaluationMetric
from app.schemas.evaluation import EvaluationInput, EvaluationRequest, MetricEvaluation
from app.services.evaluation_service import EvaluationService


def test_evaluation_request_rejects_duplicate_metrics() -> None:
    with pytest.raises(ValidationError):
        EvaluationRequest(name="duplicate metrics", metrics=[EvaluationMetric.TASK_SUCCESS, EvaluationMetric.TASK_SUCCESS], input=EvaluationInput(success=True))


def test_evaluation_request_rejects_non_positive_weight() -> None:
    with pytest.raises(ValidationError):
        EvaluationRequest(name="bad weight", metrics=[EvaluationMetric.TASK_SUCCESS], weights={EvaluationMetric.TASK_SUCCESS: 0.0}, input=EvaluationInput(success=True))


def test_evaluate_metrics_returns_all_requested_metrics() -> None:
    service = EvaluationService()
    request = EvaluationRequest(
        name="tool execution evaluation",
        metrics=[EvaluationMetric.TASK_SUCCESS, EvaluationMetric.ROUTING_ACCURACY, EvaluationMetric.TOOL_SELECTION_ACCURACY],
        input=EvaluationInput(success=True, expected_route="tool", actual_route="tool", expected_tools=["docker:list_containers"], actual_tools=["docker:list_containers"]),
    )
    results = service.evaluate_metrics(request=request)
    assert len(results) == 3
    assert all(item.passed for item in results)


def test_weighted_aggregate_score() -> None:
    score = EvaluationService.aggregate_score([
        MetricEvaluation(metric=EvaluationMetric.TASK_SUCCESS, score=1.0, passed=True, weight=2.0),
        MetricEvaluation(metric=EvaluationMetric.ROUTING_ACCURACY, score=0.5, passed=False, weight=1.0),
    ])
    assert score == pytest.approx(5 / 6)


def test_default_registry_supports_all_declared_metrics() -> None:
    service = EvaluationService()
    assert set(service.registry.supported_metrics()) == set(EvaluationMetric)
