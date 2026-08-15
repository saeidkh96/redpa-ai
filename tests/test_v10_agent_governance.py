from pathlib import Path

from app.governance_v10.schemas import AgentRunCreate, AgentRunUpdate
from app.governance_v10.service import _ALLOWED_TRANSITIONS
from app.models.governance_v10 import AgentRunStatus


def test_v10_run_schema_accepts_governed_agent_run():
    payload = AgentRunCreate(agent_id="research-agent", objective="Investigate a production incident")
    assert payload.agent_id == "research-agent"
    assert payload.input_payload == {}


def test_v10_lifecycle_contract_blocks_terminal_transitions():
    assert AgentRunStatus.RUNNING.value in _ALLOWED_TRANSITIONS[AgentRunStatus.CREATED.value]
    assert AgentRunStatus.COMPLETED.value in _ALLOWED_TRANSITIONS[AgentRunStatus.RUNNING.value]
    assert _ALLOWED_TRANSITIONS[AgentRunStatus.COMPLETED.value] == set()
    assert _ALLOWED_TRANSITIONS[AgentRunStatus.FAILED.value] == set()
    update = AgentRunUpdate(status=AgentRunStatus.BLOCKED)
    assert update.status is AgentRunStatus.BLOCKED


def test_v10_api_router_and_endpoints_are_registered():
    router = Path("backend/app/api/v1/router.py").read_text(encoding="utf-8")
    api = Path("backend/app/api/v1/governance_v10.py").read_text(encoding="utf-8")
    assert "governance_v10_router" in router
    for route in ["/runs", "/events", "/policy-check", "/evaluate"]:
        assert route in api


def test_v10_migration_follows_v9_and_creates_trace_store():
    migration = Path("backend/alembic/versions/v100a1b2c3d4e_agent_governance.py").read_text(encoding="utf-8")
    assert 'revision = "v100a1b2c3d4e"' in migration
    assert 'down_revision = "v90a1b2c3d4e"' in migration
    assert '"agent_runs"' in migration
    assert '"agent_run_events"' in migration
    assert '"evaluation_run_id"' in migration


def test_v10_reuses_existing_policy_evaluation_and_otel_layers():
    service = Path("backend/app/governance_v10/service.py").read_text(encoding="utf-8")
    assert "policy_enforcement_service.enforce" in service
    assert "EvaluationService" in service
    assert "current_trace_id" in service
    assert "current_span_id" in service
