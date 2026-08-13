from pathlib import Path


def test_v6_sdk_package_contract():
    pyproject = Path("sdk/python/pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "redpa-ai-sdk"' in pyproject
    assert 'redpa = "redpa_sdk.cli:app"' in pyproject
    assert "httpx" in pyproject
    assert "typer" in pyproject


def test_v6_cli_commands_are_real_api_surfaces():
    source = Path("sdk/python/src/redpa_sdk/cli.py").read_text(encoding="utf-8")
    assert '@app.command()' in source
    assert 'agents_app.command("list")' in source
    assert 'agents_app.command("discover")' in source
    assert 'models_app.command("providers")' in source
    assert 'tools_app.command("list")' in source
    assert 'reliability_app.command("scorecard")' in source
    assert 'quality_app.command("gate")' in source
    assert 'quality_app.command("report")' in source


def test_v6_sdk_client_only_references_existing_api_routes():
    source = Path("sdk/python/src/redpa_sdk/client.py").read_text(encoding="utf-8")
    assert "/api/v1/health" in source
    assert "/api/v1/agents" in source
    assert "/api/v1/model-gateway/providers" in source
    assert "/api/v1/tools/catalog" in source
    assert "/api/v1/model-gateway/reliability/scorecard" in source
    assert "/api/v1/evaluations/release-gates/evaluate" in source
    assert "/api/v1/evaluations/release-candidates/" in source


def test_v6_doctor_has_actionable_hints():
    source = Path("sdk/python/src/redpa_sdk/cli.py").read_text(encoding="utf-8")
    assert "Set REDPA_TOKEN" in source
    assert "docker compose up -d --build backend" in source
    assert "Error:" in source
