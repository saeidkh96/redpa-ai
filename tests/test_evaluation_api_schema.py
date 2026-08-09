from app.schemas.benchmark import BenchmarkRunRequest
from app.schemas.evaluation import EvaluationInput, EvaluationRequest


def test_benchmark_run_request() -> None:
    request = BenchmarkRunRequest.model_validate(
        {
            "name": "smoke benchmark",
            "cases": [
                {
                    "id": "case-1",
                    "name": "routing",
                    "metrics": ["routing_accuracy"],
                    "input": {
                        "expected_route": "tool",
                        "actual_route": "tool",
                    },
                }
            ],
        }
    )

    assert request.cases[0].id == "case-1"


def test_evaluation_request_accepts_string_metric_values() -> None:
    request = EvaluationRequest(
        name="api smoke",
        metrics=["task_success"],
        input=EvaluationInput(success=True),
    )

    assert request.metrics[0].value == "task_success"
