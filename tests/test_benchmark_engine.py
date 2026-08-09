from app.evaluation.benchmark import BenchmarkCase, BenchmarkEngine
from app.models.evaluation import EvaluationMetric
from app.schemas.evaluation import EvaluationInput


def test_benchmark_run_aggregates_cases() -> None:
    engine = BenchmarkEngine()

    result = engine.run(
        name="sample benchmark",
        cases=[
            BenchmarkCase(
                id="case-1",
                name="successful routing",
                metrics=[
                    EvaluationMetric.TASK_SUCCESS,
                    EvaluationMetric.ROUTING_ACCURACY,
                ],
                input=EvaluationInput(
                    success=True,
                    expected_route="tool",
                    actual_route="tool",
                ),
            ),
            BenchmarkCase(
                id="case-2",
                name="failed routing",
                metrics=[
                    EvaluationMetric.TASK_SUCCESS,
                    EvaluationMetric.ROUTING_ACCURACY,
                ],
                input=EvaluationInput(
                    success=False,
                    expected_route="tool",
                    actual_route="chat",
                ),
            ),
        ],
    )

    assert len(result.case_results) == 2
    assert result.aggregate_score == 0.5
    assert result.pass_rate == 0.5
    assert result.metric_averages["task_success"] == 0.5
    assert result.metric_averages["routing_accuracy"] == 0.5


def test_benchmark_compare_ranks_best_first() -> None:
    engine = BenchmarkEngine()

    good = engine.run(
        name="good",
        model_name="model-a",
        cases=[
            BenchmarkCase(
                id="1",
                name="case",
                metrics=[EvaluationMetric.TASK_SUCCESS],
                input=EvaluationInput(success=True),
            ),
        ],
    )

    bad = engine.run(
        name="bad",
        model_name="model-b",
        cases=[
            BenchmarkCase(
                id="1",
                name="case",
                metrics=[EvaluationMetric.TASK_SUCCESS],
                input=EvaluationInput(success=False),
            ),
        ],
    )

    comparison = engine.compare([bad, good])

    assert comparison[0]["model_name"] == "model-a"
    assert comparison[0]["rank"] == 1
