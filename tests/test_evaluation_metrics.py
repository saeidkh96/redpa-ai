import pytest

from app.evaluation.metrics import EvaluationMetricRegistry
from app.models.evaluation import EvaluationMetric
from app.schemas.evaluation import EvaluationInput


def test_task_success_metric() -> None:
    registry = EvaluationMetricRegistry()
    result = registry.evaluate(metric=EvaluationMetric.TASK_SUCCESS, evaluation_input=EvaluationInput(success=True))
    assert result.score == 1.0


def test_routing_accuracy_metric() -> None:
    registry = EvaluationMetricRegistry()
    result = registry.evaluate(metric=EvaluationMetric.ROUTING_ACCURACY, evaluation_input=EvaluationInput(expected_route="tool", actual_route="tool"))
    assert result.score == 1.0


def test_tool_selection_uses_f1() -> None:
    registry = EvaluationMetricRegistry()
    result = registry.evaluate(
        metric=EvaluationMetric.TOOL_SELECTION_ACCURACY,
        evaluation_input=EvaluationInput(expected_tools=["docker:list", "github:commits"], actual_tools=["docker:list"]),
    )
    assert result.score == pytest.approx(2 / 3)
    assert result.details["precision"] == 1.0
    assert result.details["recall"] == 0.5


def test_response_relevance_is_bounded() -> None:
    registry = EvaluationMetricRegistry()
    result = registry.evaluate(metric=EvaluationMetric.RESPONSE_RELEVANCE, evaluation_input=EvaluationInput(request_text="inspect docker containers", response_text="docker containers are running"))
    assert 0.0 <= result.score <= 1.0
    assert result.score > 0.0


def test_rag_faithfulness_supports_matching_claim() -> None:
    registry = EvaluationMetricRegistry()
    result = registry.evaluate(metric=EvaluationMetric.RAG_FAITHFULNESS, evaluation_input=EvaluationInput(claims=["RedPA supports durable workflows"], contexts=["RedPA supports durable workflows and workflow resume."]))
    assert result.score == 1.0


def test_context_relevance_is_bounded() -> None:
    registry = EvaluationMetricRegistry()
    result = registry.evaluate(metric=EvaluationMetric.CONTEXT_RELEVANCE, evaluation_input=EvaluationInput(request_text="agent memory semantic search", contexts=["Agent memory supports semantic search with Qdrant.", "Docker containers can be inspected with MCP."]))
    assert 0.0 <= result.score <= 1.0
    assert result.score > 0.0


def test_latency_score_degrades_after_target() -> None:
    registry = EvaluationMetricRegistry()
    result = registry.evaluate(metric=EvaluationMetric.LATENCY, evaluation_input=EvaluationInput(latency_ms=2000, latency_target_ms=1000))
    assert result.score == 0.5


def test_token_usage_score_degrades_after_budget() -> None:
    registry = EvaluationMetricRegistry()
    result = registry.evaluate(metric=EvaluationMetric.TOKEN_USAGE, evaluation_input=EvaluationInput(input_tokens=600, output_tokens=400, token_budget=500))
    assert result.score == 0.5


def test_cost_score_degrades_after_budget() -> None:
    registry = EvaluationMetricRegistry()
    result = registry.evaluate(metric=EvaluationMetric.COST, evaluation_input=EvaluationInput(cost_usd=0.04, cost_budget_usd=0.02))
    assert result.score == 0.5
