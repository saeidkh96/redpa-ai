from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_chat_uses_governed_orchestrator():
    source = read("backend/app/services/chat_service.py")
    assert "GovernedOrchestratorService.run" in source
    assert "GovernedOrchestratorService.stream" in source


def test_governed_runtime_persists_lifecycle_and_evaluation():
    source = read("backend/app/services/governed_orchestrator_service.py")
    assert "create_run" in source
    assert "AgentRunStatus.RUNNING" in source
    assert "AgentRunStatus.COMPLETED" in source
    assert "AgentRunStatus.FAILED" in source
    assert "evaluate_run" in source


def test_agent_nodes_emit_governance_events():
    planner = read("backend/app/agents/nodes/planner.py")
    research = read("backend/app/agents/nodes/research.py")
    human = read("backend/app/agents/nodes/human_review.py")
    assert 'event_type="planner.decision"' in planner
    assert 'event_type="research.started"' in research
    assert 'event_type="research.completed"' in research
    assert 'event_type="hitl.requested"' in human


def test_tool_node_enforces_governance_policy():
    source = read("backend/app/agents/nodes/tool.py")
    assert "runtime_policy_check" in source
    assert 'event_type="tool.blocked"' in source
    assert 'event_type="tool.execution_started"' in source
    assert 'event_type="tool.execution_completed"' in source
