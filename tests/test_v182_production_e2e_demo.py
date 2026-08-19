from app.production_demo_v182.schemas import ProductionDemoRequest
from app.production_demo_v182.service import _DESTRUCTIVE


def test_v182_default_demo_is_safe_and_failure_injected():
    payload = ProductionDemoRequest()
    assert payload.inject_primary_failure is True
    assert payload.fallback_agent == "docker-agent"
    assert _DESTRUCTIVE.search(payload.task) is None


def test_v182_destructive_actions_require_boundary():
    assert _DESTRUCTIVE.search("restart container redpa-backend") is not None
    assert _DESTRUCTIVE.search("list running containers") is None
