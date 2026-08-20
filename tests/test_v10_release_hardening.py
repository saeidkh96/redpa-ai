from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_policy_service_is_first_class_compose_dependency():
    compose = read("docker-compose.yml")
    assert "\n  policy-service:\n" in compose
    assert "POLICY_SERVICE_URL: http://policy-service:8090" in compose
    assert "policy-service:\n        condition: service_healthy" in compose
    assert "http://localhost:8090/actuator/health" in compose


def test_observability_services_restart_and_backend_waits_for_collector_start():
    compose = read("docker-compose.yml")
    otel = compose[compose.index("  otel-collector:"):compose.index("  tempo:")]
    tempo = compose[compose.index("  tempo:"):compose.index("  redis:")]
    assert "restart: unless-stopped" in otel
    assert "restart: unless-stopped" in tempo
    assert "otel-collector:\n        condition: service_started" in compose


def test_v10_machine_readable_versions_are_consistent():
    assert 'default="19.2.0"' in read("backend/app/core/config.py")
    assert 'APP_VERSION: "19.2.0"' in read("docker-compose.yml")
    assert "version='19.2.0'" in read("backend/app/ops_v9/agent_server.py")
    assert "'version':'19.2.0'" in read("backend/app/ops_v9/agent_server.py")
    assert json.loads(read("frontend/package.json"))["version"] == "19.2.0"
    assert 'version = "19.2.0"' in read("sdk/python/pyproject.toml")
    assert 'appVersion: "19.2.0"' in read("deploy/helm/redpa/Chart.yaml")
    assert 'APP_VERSION: "19.2.0"' in read(".github/workflows/ci.yml")


def test_v10_gate_runs_phase3_lifecycle_and_full_regression():
    gate = read(".github/workflows/v10-governance-gate.yml")
    assert 'APP_VERSION: "19.2.0"' in gate
    assert "tests/test_v10_agent_governance.py" in gate
    assert "python -m pytest tests -q" in gate
