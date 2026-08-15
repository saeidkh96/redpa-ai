from pathlib import Path

from app.ops_v9.cost import CostEstimator
from app.ops_v9.readiness import ReleaseReadinessEvaluator
from app.ops_v9.schemas import CostEstimateRequest, ReleaseReadinessRequest


def test_v9_cost_estimator_is_deterministic():
    result = CostEstimator.estimate(CostEstimateRequest(backend_replicas=2, worker_replicas=2))
    assert result.backend_eur == 110.0
    assert result.workers_eur == 80.0
    assert result.monthly_total_eur == 440.0
    assert result.annual_total_eur == 5280.0


def test_v9_release_readiness_promotes_only_when_all_gates_pass():
    passed = ReleaseReadinessEvaluator.evaluate(ReleaseReadinessRequest(availability=0.999, p95_latency_ms=400))
    assert passed.decision == 'PROMOTE'
    held = ReleaseReadinessEvaluator.evaluate(ReleaseReadinessRequest(availability=0.95, p95_latency_ms=1200, open_critical_incidents=1))
    assert held.decision == 'HOLD'
    assert set(held.reasons) >= {'availability','p95_latency','critical_incidents'}


def test_v9_ops_agent_enforces_hitl_and_stateful_denylist_contract():
    source = Path('backend/app/ops_v9/agent_server.py').read_text(encoding='utf-8')
    assert "_STATEFUL_DENY = {'redpa-postgres','redpa-qdrant','redpa-redis'}" in source
    assert 'if not payload.approved' in source
    assert "Automatic restart is disabled for stateful data services" in source


def test_v9_api_and_migration_contract():
    router = Path('backend/app/api/v1/router.py').read_text(encoding='utf-8')
    api = Path('backend/app/api/v1/operations_v9.py').read_text(encoding='utf-8')
    migration = Path('backend/alembic/versions/v90a1b2c3d4e_ops_incidents.py').read_text(encoding='utf-8')
    assert 'operations_v9_router' in router
    for route in ['/incidents','/cost/estimate','/release/readiness']:
        assert route in api
    assert "revision = 'v90a1b2c3d4e'" in migration
    assert "down_revision = 'v80a1b2c3d4e'" in migration
    assert "'ops_incidents'" in migration
    assert "'ops_actions'" in migration


def test_v9_compose_registers_ops_agent_with_docker_socket_and_healthcheck():
    compose = Path('docker-compose.yml').read_text(encoding='utf-8')
    assert 'ops-agent:' in compose
    assert 'app.ops_v9.agent_server' in compose
    assert '/var/run/docker.sock:/var/run/docker.sock' in compose
    assert 'http://ops-agent:8070' in compose
    assert '127.0.0.1:8070/health' in compose


def test_v9_control_plane_routes_exist():
    for rel in [
        'frontend/app/control-plane/incidents/page.tsx',
        'frontend/app/control-plane/cloud/page.tsx',
        'frontend/app/control-plane/cost/page.tsx',
    ]:
        assert Path(rel).exists()
    shell = Path('frontend/components/control-plane/ControlPlaneShell.tsx').read_text(encoding='utf-8')
    assert '/control-plane/incidents' in shell
    assert '/control-plane/cloud' in shell
    assert '/control-plane/cost' in shell


def test_v9_backup_restore_require_explicit_confirmation_for_restore():
    restore = Path('scripts/operations/postgres_restore.py').read_text(encoding='utf-8')
    assert "parser.add_argument('--confirm', action='store_true')" in restore
    assert 'Refusing restore without --confirm.' in restore
