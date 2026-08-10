from __future__ import annotations

from pathlib import Path

import pytest

from app.model_gateway.contracts import LLMMessage, LLMRequest
from app.model_gateway.gateway import ModelGateway
from app.model_gateway.providers.mock import MockLLMProvider
from app.model_gateway.registry import LLMProviderRegistry, ProviderNotFoundError
from app.services.platform_v4_model_governance_service import ModelPricingCatalog, current_period_key
from app.services.platform_v4_workflow_service import ALLOWED_TRANSITIONS


ROOT = Path(__file__).resolve().parents[2]


def test_pricing_catalog_calculates_input_and_output_cost() -> None:
    catalog = ModelPricingCatalog(
        {
            "mock:mock-model": {
                "input_per_1k": 0.1,
                "output_per_1k": 0.2,
            }
        }
    )
    assert catalog.estimate(
        provider="mock",
        model="mock-model",
        input_tokens=1000,
        output_tokens=500,
    ) == pytest.approx(0.2)


def test_period_key_is_year_month() -> None:
    assert len(current_period_key()) == 7
    assert current_period_key()[4] == "-"


def test_workflow_state_machine_prevents_terminal_resume() -> None:
    assert "paused" in ALLOWED_TRANSITIONS["running"]
    assert "running" in ALLOWED_TRANSITIONS["paused"]
    assert not ALLOWED_TRANSITIONS["completed"]
    assert not ALLOWED_TRANSITIONS["cancelled"]


@pytest.mark.asyncio
async def test_model_gateway_can_restrict_candidates_by_tenant_allowlist() -> None:
    registry = LLMProviderRegistry(default_provider="mock")
    registry.register(MockLLMProvider(name="mock"))
    gateway = ModelGateway(registry=registry)

    request = LLMRequest(messages=(LLMMessage(role="user", content="hello"),))
    result = await gateway.invoke(request=request, allowed_providers={"mock"})
    assert result.response.provider == "mock"

    with pytest.raises(ProviderNotFoundError):
        await gateway.invoke(request=request, allowed_providers={"other"})


def test_v4_1_migration_is_chained_after_phase_17() -> None:
    migration = (
        ROOT
        / "backend"
        / "alembic"
        / "versions"
        / "p20v41a1b2c3_platform_v4_control_plane.py"
    ).read_text(encoding="utf-8")
    assert 'down_revision = "p17a1b2c3d4e"' in migration
    assert '"platform_model_budgets"' in migration
    assert '"platform_workflow_runs"' in migration
    assert '"platform_event_deliveries"' in migration


def test_model_gateway_request_accepts_optional_tenant_id() -> None:
    from app.schemas.model_gateway import GatewayInvokeRequest

    request = GatewayInvokeRequest.model_validate(
        {
            "messages": [{"role": "user", "content": "hello"}],
        }
    )
    assert request.tenant_id is None
