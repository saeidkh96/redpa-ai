from __future__ import annotations
from datetime import datetime, timezone
import pytest
from app.a2a.registry import agent_registry
from app.a2a.schemas import AgentCapability, AgentCard, AgentEndpoint, AgentStatus
from app.a2a.service import AgentService
from app.self_healing.routing import HealthAwareAgentRouter

def card(agent_id,status):
    now=datetime.now(timezone.utc)
    return AgentCard(id=agent_id,name=agent_id,version="1.0.0",description="test",status=status,capabilities=[AgentCapability(name="research",description="Research capability",tags=["research"],examples=["research"])],supported_routes=[],endpoint=AgentEndpoint(url=f"http://{agent_id}:8000"),metadata={},registered_at=now,updated_at=now)

@pytest.fixture(autouse=True)
def isolate_registry():
    original=dict(agent_registry._agents); initialized=AgentService._initialized
    agent_registry._agents.clear(); AgentService._initialized=True
    try: yield
    finally:
        agent_registry._agents.clear(); agent_registry._agents.update(original); AgentService._initialized=initialized

@pytest.mark.asyncio
async def test_healthy_preferred():
    await agent_registry.register(card("research-degraded",AgentStatus.DEGRADED))
    await agent_registry.register(card("research-healthy",AgentStatus.ACTIVE))
    d=await HealthAwareAgentRouter().select("research")
    assert d.selected_agent_id=="research-healthy"

@pytest.mark.asyncio
async def test_degraded_fallback():
    await agent_registry.register(card("research-degraded",AgentStatus.DEGRADED))
    d=await HealthAwareAgentRouter().select("research")
    assert d.selected_agent_id=="research-degraded"

@pytest.mark.asyncio
async def test_offline_excluded():
    await agent_registry.register(card("research-offline",AgentStatus.OFFLINE))
    d=await HealthAwareAgentRouter().select("research")
    assert d.selected_agent_id is None
