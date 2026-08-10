from app.platform_v4.agent_runtime import AgentDefinition, AgentRuntimeRegistry
from app.platform_v4.event_platform import EventEnvelope, EventPlatform
from app.platform_v4.model_governance import ModelBudget
from app.platform_v4.policy_platform import PolicyPlatform, PolicyRule
from app.platform_v4.tool_platform import ToolDefinition, ToolPlatform

def test_model_budget_blocks_overage():
    b=ModelBudget("t1",100,1.0,allowed_providers={"ollama"}); assert b.can_spend(50,.2,"ollama")[0]; assert not b.can_spend(101,.2,"ollama")[0]; assert not b.can_spend(1,.1,"other")[0]
def test_agent_discovery_by_capability():
    r=AgentRuntimeRegistry(); r.register(AgentDefinition("research","1",("search","summarize"))); assert r.discover("search")[0].agent_id=="research"
def test_tool_approval_gate():
    p=ToolPlatform(); p.register(ToolDefinition("send-email","mcp",approval_required=True)); assert p.authorize("send-email",set())[1]=="human_approval_required"
def test_policy_defaults_deny_and_versions():
    p=PolicyPlatform(); assert p.evaluate("t","deploy","high")["effect"]=="deny"; p.publish(PolicyRule("deploy","t",2,"deploy","approve",("high",),2)); assert p.evaluate("t","deploy","high")["required_approvals"]==2
def test_event_moves_to_dlq_and_replays():
    p=EventPlatform(); p.publish(EventEnvelope("e1","jobs","t")); p.fail("e1","boom",1); assert p.dlq.get("e1") is not None; p.replay("e1"); assert p.dlq.get("e1") is None and p.events.get("e1").status=="pending"
