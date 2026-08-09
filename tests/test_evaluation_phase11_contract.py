from app.evaluation.metrics import EvaluationMetricRegistry
from app.evaluation.telemetry import evaluation_telemetry
from app.models.evaluation import EvaluationMetric
from app.schemas.evaluation import EvaluationInput, EvaluationRequest
from app.services.evaluation_service import EvaluationService


def test_phase11_declares_nine_metrics() -> None:
    assert len(EvaluationMetric) == 9


def test_phase11_registry_matches_metric_enum() -> None:
    registry = EvaluationMetricRegistry()

    assert set(registry.supported_metrics()) == set(EvaluationMetric)


def test_phase11_sample_score_matches_expected_baseline() -> None:
    evaluation_telemetry.reset_for_tests()

    service = EvaluationService()

    request = EvaluationRequest(
        name="RedPA evaluation sample",
        metrics=[
            EvaluationMetric.TASK_SUCCESS,
            EvaluationMetric.ROUTING_ACCURACY,
            EvaluationMetric.TOOL_SELECTION_ACCURACY,
            EvaluationMetric.RESPONSE_RELEVANCE,
            EvaluationMetric.LATENCY,
        ],
        input=EvaluationInput(
            request_text="Inspect Docker containers",
            response_text="The Docker containers are running.",
            success=True,
            expected_route="tool",
            actual_route="tool",
            expected_tools=["mcp:redpa-docker:list_containers"],
            actual_tools=["mcp:redpa-docker:list_containers"],
            latency_ms=850,
            latency_target_ms=1500,
        ),
        pass_threshold=0.7,
    )

    results = service.evaluate_metrics(request=request)
    score = service.aggregate_score(results)

    assert round(score, 3) == 0.867
    assert all(
        result.passed
        for result in results
        if result.metric != EvaluationMetric.RESPONSE_RELEVANCE
    )


def test_phase11_all_metric_scores_are_bounded() -> None:
    service = EvaluationService()

    request = EvaluationRequest(
        name="all metrics",
        metrics=list(EvaluationMetric),
        input=EvaluationInput(
            request_text="RedPA uses semantic memory",
            response_text="RedPA uses semantic memory.",
            success=True,
            expected_route="rag",
            actual_route="rag",
            expected_tools=[],
            actual_tools=[],
            contexts=["RedPA uses semantic memory with Qdrant."],
            claims=["RedPA uses semantic memory."],
            latency_ms=500,
            latency_target_ms=1000,
            input_tokens=100,
            output_tokens=50,
            token_budget=500,
            cost_usd=0.01,
            cost_budget_usd=0.05,
        ),
    )

    results = service.evaluate_metrics(request=request)

    assert len(results) == 9
    assert all(0.0 <= item.score <= 1.0 for item in results)
