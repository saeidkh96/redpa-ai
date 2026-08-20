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


def test_v6_full_cli_surface_contract():
    source = Path("sdk/python/src/redpa_sdk/cli.py").read_text(encoding="utf-8")
    for fragment in [
        'workflows_app.command("list")',
        'workflows_app.command("create")',
        'workflows_app.command("resume")',
        'reviews_app.command("list")',
        'reviews_app.command("approve")',
        'reviews_app.command("reject")',
        'reviews_app.command("resume")',
        'mcp_app.command("servers")',
        'mcp_app.command("health")',
        'mcp_app.command("tools")',
        'mcp_app.command("execute")',
    ]:
        assert fragment in source


def test_v6_async_client_and_release_version_contract():
    init_source = Path("sdk/python/src/redpa_sdk/__init__.py").read_text(encoding="utf-8")
    project = Path("sdk/python/pyproject.toml").read_text(encoding="utf-8")
    workflow = Path(".github/workflows/sdk-ci.yml").read_text(encoding="utf-8")
    assert "AsyncRedPA" in init_source
    assert '__version__ = "19.1.0"' in init_source
    assert 'version = "19.1.0"' in project
    assert 'python-version: ["3.11", "3.12", "3.13"]' in workflow
    assert "python -m build sdk/python" in workflow


def test_v6_sync_client_routes_match_implemented_backend():
    source = Path("sdk/python/src/redpa_sdk/client.py").read_text(encoding="utf-8")
    for route in [
        "/api/v1/agents/distributed/durable",
        "/api/v1/reviews",
        "/api/v1/mcp/servers",
        "/api/v1/mcp/health",
        "/api/v1/mcp/tools",
        "/api/v1/mcp/tools/execute",
        "/api/v1/evaluations/benchmark-suites",
        "/api/v1/model-gateway/reliability/history",
    ]:
        assert route in source


def test_v7_research_sdk_contract():
    client = Path("sdk/python/src/redpa_sdk/client.py").read_text(encoding="utf-8")
    async_client = Path("sdk/python/src/redpa_sdk/async_client.py").read_text(encoding="utf-8")
    cli = Path("sdk/python/src/redpa_sdk/cli.py").read_text(encoding="utf-8")
    assert "/api/v1/research/runs" in client
    assert "/api/v1/research/runs" in async_client
    assert 'app.add_typer(research_app, name="research")' in cli
    assert '@research_app.command("start")' in cli
    assert '@research_app.command("list")' in cli
    assert '@research_app.command("get")' in cli
