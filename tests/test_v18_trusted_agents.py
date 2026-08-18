from app.trusted_agents_v18.engine import trusted_agent_engine
from app.trusted_agents_v18.schemas import TrustedAgentInput
def test_v18_trusted():
 r=trusted_agent_engine.evaluate(TrustedAgentInput(agent_id="a",version="1",capabilities=["research"],signed_manifest=True,health_endpoint=True,governance_compatible=True,provenance_verified=True,policy_profile=True)); assert r.routable
def test_v18_untrusted_not_routable():
 r=trusted_agent_engine.evaluate(TrustedAgentInput(agent_id="a",version="1")); assert not r.routable
