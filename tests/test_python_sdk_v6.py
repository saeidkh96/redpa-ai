from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx
import pytest

SDK_SRC = Path("sdk/python/src").resolve()
if str(SDK_SRC) not in sys.path:
    sys.path.insert(0, str(SDK_SRC))

from redpa_sdk import RedPA, RedPAConfig, RedPAError


def transport(handler):
    return httpx.MockTransport(handler)


def test_sdk_health_and_authorization_header():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/health"
        assert request.headers["authorization"] == "Bearer test-token"
        return httpx.Response(
            200,
            json={
                "status": "healthy",
                "service": "RedPA AI",
                "version": "6.0.0",
                "environment": "test",
                "database": {"status": "healthy"},
            },
        )

    with RedPA(
        RedPAConfig(base_url="http://redpa.test", token="test-token"),
        transport=transport(handler),
    ) as client:
        result = client.health()

    assert result.status == "healthy"
    assert result.database.status == "healthy"


def test_sdk_agent_discovery_uses_real_route_contract():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/agents/discover"
        assert request.url.params["query"] == "research"
        assert request.url.params["limit"] == "3"
        return httpx.Response(
            200,
            json={"query": "research", "matches": [], "total": 0},
        )

    with RedPA(
        RedPAConfig(base_url="http://redpa.test"),
        transport=transport(handler),
    ) as client:
        result = client.discover_agents("research", limit=3)

    assert result["total"] == 0


def test_sdk_provider_models_validate_backend_payload():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/model-gateway/providers"
        return httpx.Response(
            200,
            json=[
                {
                    "name": "ollama",
                    "provider_type": "ollama",
                    "default_model": "qwen2.5:7b",
                    "capabilities": ["chat"],
                    "enabled": True,
                }
            ],
        )

    with RedPA(
        RedPAConfig(base_url="http://redpa.test"),
        transport=transport(handler),
    ) as client:
        providers = client.providers()

    assert providers[0].name == "ollama"
    assert providers[0].enabled is True


def test_sdk_tool_catalog_matches_backend_shape():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/tools/catalog"
        assert request.url.params["refresh"] == "true"
        return httpx.Response(
            200,
            json={
                "items": [],
                "total": 0,
                "internal_total": 0,
                "mcp_total": 0,
                "mcp_server_errors": {},
                "refreshed_at": "2026-08-13T20:00:00Z",
            },
        )

    with RedPA(
        RedPAConfig(base_url="http://redpa.test"),
        transport=transport(handler),
    ) as client:
        catalog = client.tools(refresh=True)

    assert catalog.total == 0
    assert catalog.mcp_total == 0


def test_sdk_release_gate_posts_persisted_release_endpoint():
    baseline = "550e8400-e29b-41d4-a716-446655440000"
    candidate = "7c9e6679-7425-40de-944b-e07fc1f90ae7"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/evaluations/release-gates/evaluate"
        body = json.loads(request.content)
        assert body["baseline_run_id"] == baseline
        assert body["candidate_run_id"] == candidate
        assert body["release_label"] == "v6-sdk"
        assert body["metadata"]["source"] == "python_sdk"
        return httpx.Response(
            200,
            json={
                "id": "8f14e45f-ea4e-4c8d-9f7e-123456789abc",
                "decision": "PASS",
                "reasons": ["quality_gate_passed"],
                "release_label": "v6-sdk",
                "regression": {
                    "baseline_run_id": baseline,
                    "candidate_run_id": candidate,
                    "baseline_score": 0.8,
                    "candidate_score": 0.85,
                    "aggregate_delta": 0.05,
                    "metric_deltas": [],
                    "regressed_metrics": [],
                    "regression_detected": False,
                },
                "created_at": "2026-08-13T20:00:00Z",
            },
        )

    with RedPA(
        RedPAConfig(base_url="http://redpa.test"),
        transport=transport(handler),
    ) as client:
        result = client.release_gate(
            baseline_run_id=baseline,
            candidate_run_id=candidate,
            release_label="v6-sdk",
        )

    assert result.decision == "PASS"


def test_sdk_error_exposes_status_and_detail():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"detail": "forbidden"})

    with RedPA(
        RedPAConfig(base_url="http://redpa.test"),
        transport=transport(handler),
    ) as client:
        with pytest.raises(RedPAError) as exc:
            client.providers()

    assert exc.value.status_code == 403
    assert exc.value.detail == "forbidden"


def test_sdk_config_from_env(monkeypatch):
    monkeypatch.setenv("REDPA_API_URL", "http://localhost:9999/")
    monkeypatch.setenv("REDPA_TOKEN", "abc")
    monkeypatch.setenv("REDPA_TIMEOUT_SECONDS", "12.5")
    config = RedPAConfig.from_env()
    assert config.base_url == "http://localhost:9999"
    assert config.token == "abc"
    assert config.timeout_seconds == 12.5


def test_sdk_connection_error_is_wrapped():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with RedPA(
        RedPAConfig(base_url="http://redpa.test"),
        transport=transport(handler),
    ) as client:
        with pytest.raises(RedPAError) as exc:
            client.health()

    assert "Cannot connect to RedPA API" in str(exc.value)
    assert exc.value.status_code is None
    assert exc.value.detail["type"] == "ConnectError"
    assert "Start or rebuild" in exc.value.detail["hint"]


def test_sdk_workflow_and_review_routes():
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        if request.url.path == "/api/v1/agents/distributed/durable":
            return httpx.Response(200, json=[])
        if request.url.path == "/api/v1/reviews":
            return httpx.Response(
                200,
                json={"items": [], "total": 0, "limit": 20, "offset": 0},
            )
        raise AssertionError(request.url.path)

    with RedPA(
        RedPAConfig(base_url="http://redpa.test"),
        transport=transport(handler),
    ) as client:
        assert client.workflows() == []
        assert client.reviews()["total"] == 0

    assert ("GET", "/api/v1/agents/distributed/durable") in seen
    assert ("GET", "/api/v1/reviews") in seen


def test_sdk_mcp_execute_uses_qualified_execute_route():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/mcp/tools/execute"
        body = json.loads(request.content)
        assert body == {
            "qualified_name": "mcp:filesystem:read_file",
            "arguments": {"path": "README.md"},
            "approval_granted": True,
        }
        return httpx.Response(
            200,
            json={
                "server_name": "filesystem",
                "tool_name": "read_file",
                "success": True,
                "is_error": False,
                "content": [],
                "structured_content": None,
                "execution_time_ms": 1.0,
            },
        )

    with RedPA(
        RedPAConfig(base_url="http://redpa.test"),
        transport=transport(handler),
    ) as client:
        result = client.execute_mcp_tool(
            "mcp:filesystem:read_file",
            arguments={"path": "README.md"},
            approval_granted=True,
        )

    assert result["success"] is True


@pytest.mark.asyncio
async def test_async_sdk_health():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/health"
        return httpx.Response(
            200,
            json={
                "status": "healthy",
                "service": "RedPA AI",
                "version": "6.0.0",
                "environment": "test",
                "database": {"status": "healthy"},
            },
        )

    from redpa_sdk import AsyncRedPA

    async with AsyncRedPA(
        RedPAConfig(base_url="http://redpa.test"),
        transport=httpx.MockTransport(handler),
    ) as client:
        result = await client.health()

    assert result.status == "healthy"
