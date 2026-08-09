from app.evaluation.telemetry import EvaluationTelemetry


def test_evaluation_telemetry_tracks_runs() -> None:
    telemetry = EvaluationTelemetry()

    telemetry.run_started()
    telemetry.metric_recorded(
        metric="task_success",
        score=1.0,
        passed=True,
    )
    telemetry.run_completed(0.9)

    snapshot = telemetry.snapshot()

    assert snapshot["runs"]["total"] == 1
    assert snapshot["runs"]["completed"] == 1
    assert snapshot["runs"]["failed"] == 0
    assert snapshot["runs"]["active"] == 0
    assert snapshot["runs"]["average_aggregate_score"] == 0.9


def test_evaluation_telemetry_tracks_failed_run() -> None:
    telemetry = EvaluationTelemetry()

    telemetry.run_started()
    telemetry.run_failed()

    snapshot = telemetry.snapshot()

    assert snapshot["runs"]["total"] == 1
    assert snapshot["runs"]["failed"] == 1
    assert snapshot["runs"]["active"] == 0


def test_evaluation_telemetry_tracks_metric_scores() -> None:
    telemetry = EvaluationTelemetry()

    telemetry.metric_recorded(
        metric="routing_accuracy",
        score=1.0,
        passed=True,
    )
    telemetry.metric_recorded(
        metric="routing_accuracy",
        score=0.0,
        passed=False,
    )

    metric = telemetry.snapshot()["metrics"]["routing_accuracy"]

    assert metric["count"] == 2
    assert metric["passed"] == 1
    assert metric["failed"] == 1
    assert metric["average_score"] == 0.5


def test_evaluation_telemetry_tracks_benchmarks() -> None:
    telemetry = EvaluationTelemetry()

    telemetry.benchmark_completed(
        aggregate_score=0.75,
        case_passes=[True, False, True, True],
    )

    snapshot = telemetry.snapshot()

    assert snapshot["benchmarks"]["runs"] == 1
    assert snapshot["benchmarks"]["cases"] == 4
    assert snapshot["benchmarks"]["passed_cases"] == 3
    assert snapshot["benchmarks"]["pass_rate"] == 0.75
