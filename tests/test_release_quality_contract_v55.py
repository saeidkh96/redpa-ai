from pathlib import Path


def test_release_quality_api_contract():
    source = Path("backend/app/api/v1/evaluations.py").read_text(encoding="utf-8")
    assert '"/release-gates/evaluate"' in source
    assert '"/release-gates/ci-check"' in source
    assert '"/release-gates"' in source
    assert '"/benchmark-trends"' in source
    assert "HTTP_409_CONFLICT" in source


def test_release_quality_routes_precede_dynamic_run_route():
    source = Path("backend/app/api/v1/evaluations.py").read_text(encoding="utf-8")
    dynamic = source.index('"/{run_id}"')
    assert source.index('"/release-gates/evaluate"') < dynamic
    assert source.index('"/benchmark-trends"') < dynamic


def test_release_quality_migration_chains_from_batch2():
    source = Path("backend/alembic/versions/r55q3a4b5c6d_create_release_quality_gates.py").read_text(encoding="utf-8")
    assert 'down_revision = "b55a2c3d4e5f"' in source
