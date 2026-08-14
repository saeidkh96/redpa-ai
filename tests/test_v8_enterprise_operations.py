from pathlib import Path

from app.analytics_v8.schemas import AnalyticsEventBatch, AnalyticsEventCreate, KPIQueryRequest
from app.connectors_v8.schemas import ConnectorCreate, ConnectorExecuteRequest
from app.reliability_v8.slo import SLOEvaluateRequest, SLOEvaluator


def test_v8_analytics_supports_weighted_kpis_and_dimensions():
    batch = AnalyticsEventBatch(items=[AnalyticsEventCreate(metric="staffing.fill_rate", value=0.8, weight=10, dimensions={"business_unit":"sales"})])
    query = KPIQueryRequest(metric="staffing.fill_rate", aggregation="weighted_avg", group_by=["business_unit"])
    assert batch.items[0].weight == 10
    assert query.aggregation == "weighted_avg"
    assert query.group_by == ["business_unit"]


def test_v8_connector_contract_is_approval_aware():
    connector = ConnectorCreate(name="n8n", kind="n8n_webhook", endpoint_url="https://example.com/webhook")
    dry_run = ConnectorExecuteRequest(payload={"event":"test"})
    live = ConnectorExecuteRequest(payload={"event":"test"}, dry_run=False, approval_granted=True)
    assert connector.kind == "n8n_webhook"
    assert dry_run.dry_run is True
    assert live.approval_granted is True


def test_v8_slo_evaluator_passes_good_release_evidence():
    payload = SLOEvaluateRequest(
        samples=[{"latency_ms": 200 + index, "success": True} for index in range(100)],
        availability_target=0.99,
        p95_latency_target_ms=500,
    )
    result = SLOEvaluator.evaluate(payload)
    assert result.decision == "PASS"
    assert result.availability == 1.0
    assert result.p95_latency_ms < 500


def test_v8_slo_evaluator_fails_bad_availability():
    payload = SLOEvaluateRequest(
        samples=[{"latency_ms": 100, "success": index < 95} for index in range(100)],
        availability_target=0.99,
        p95_latency_target_ms=500,
    )
    result = SLOEvaluator.evaluate(payload)
    assert result.decision == "FAIL"
    assert result.availability_passed is False


def test_v8_routes_are_registered():
    router = Path("backend/app/api/v1/router.py").read_text(encoding="utf-8")
    assert "analytics_v8_router" in router
    assert "connectors_v8_router" in router
    assert "operations_v8_router" in router


def test_v8_control_plane_pages_exist():
    assert Path("frontend/app/control-plane/analytics/page.tsx").exists()
    assert Path("frontend/app/control-plane/connectors/page.tsx").exists()
    assert Path("frontend/app/control-plane/operations/page.tsx").exists()
    shell = Path("frontend/components/control-plane/ControlPlaneShell.tsx").read_text(encoding="utf-8")
    assert "/control-plane/analytics" in shell
    assert "/control-plane/connectors" in shell
    assert "/control-plane/operations" in shell


def test_v8_migration_extends_v7_head():
    migration = Path("backend/alembic/versions/v80a1b2c3d4e_analytics_connectors.py").read_text(encoding="utf-8")
    assert 'revision = "v80a1b2c3d4e"' in migration
    assert 'down_revision = "v70a1b2c3d4e"' in migration
    assert "analytics_fact_events" in migration
    assert "enterprise_connectors" in migration
    assert "connector_deliveries" in migration


def test_v8_cloud_reliability_assets_exist():
    assert Path("scripts/reliability/load_test.py").exists()
    assert Path("config/slo-v8.yaml").exists()
    assert Path("infra/azure/Pulumi.prod.yaml.example").exists()
    assert Path(".github/workflows/azure-production-deploy.yml").exists()
    assert Path(".github/workflows/v8-reliability-smoke.yml").exists()
