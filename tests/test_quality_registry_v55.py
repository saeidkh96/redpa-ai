from __future__ import annotations

from pathlib import Path

from app.models.quality_registry import BenchmarkSuiteRecord, ReliabilitySnapshotRecord
from app.schemas.benchmark import BenchmarkCaseRequest
from app.schemas.evaluation import EvaluationInput
from app.models.evaluation import EvaluationMetric
from app.schemas.quality_registry import BenchmarkSuiteCreateRequest


def test_quality_registry_model_contracts():
    assert BenchmarkSuiteRecord.__tablename__ == "benchmark_suites"
    assert ReliabilitySnapshotRecord.__tablename__ == "reliability_snapshots"
    suite_columns = {column.name for column in BenchmarkSuiteRecord.__table__.columns}
    reliability_columns = {column.name for column in ReliabilitySnapshotRecord.__table__.columns}
    assert {"id", "name", "cases", "pass_threshold", "enabled", "metadata"}.issubset(suite_columns)
    assert {"id", "overall_score", "healthy_providers", "degraded_providers", "unavailable_providers", "providers"}.issubset(reliability_columns)


def test_benchmark_suite_schema_serializes_reusable_case():
    request = BenchmarkSuiteCreateRequest(
        name="release-smoke",
        cases=[
            BenchmarkCaseRequest(
                id="case-1",
                name="Answer quality",
                input=EvaluationInput(
                    request_text="What is RedPA?",
                    response_text="An agentic AI platform.",
                ),
                metrics=[EvaluationMetric.RESPONSE_RELEVANCE],
            )
        ],
    )
    payload = request.model_dump(mode="json")
    assert payload["name"] == "release-smoke"
    assert payload["cases"][0]["metrics"] == ["response_relevance"]


def test_batch4_api_contract():
    evaluation_api = Path("backend/app/api/v1/evaluations.py").read_text(encoding="utf-8")
    gateway_api = Path("backend/app/api/v1/model_gateway.py").read_text(encoding="utf-8")
    assert '"/benchmark-suites"' in evaluation_api
    assert '"/benchmark-suites/{suite_id}/run"' in evaluation_api
    assert '"/release-candidates/{candidate_run_id}/report"' in evaluation_api
    assert '"/reliability/capture"' in gateway_api
    assert '"/reliability/history"' in gateway_api


def test_batch4_migration_chains_from_batch3():
    source = Path("backend/alembic/versions/q55b4c5d6e7f_create_quality_registry.py").read_text(encoding="utf-8")
    assert 'down_revision = "r55q3a4b5c6d"' in source
