from app.models.benchmark import BenchmarkRunRecord


def test_benchmark_run_record_contract():
    assert BenchmarkRunRecord.__tablename__ == "benchmark_runs"
    columns = {column.name for column in BenchmarkRunRecord.__table__.columns}
    assert {
        "id",
        "name",
        "agent_id",
        "model_name",
        "aggregate_score",
        "pass_rate",
        "pass_threshold",
        "metric_averages",
        "case_results",
        "created_at",
    }.issubset(columns)
