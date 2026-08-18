from .schemas import TrustedAgentInput,TrustDecision
class TrustedAgentEngine:
    def evaluate(self,x:TrustedAgentInput)->TrustDecision:
        checks={"signed_manifest":x.signed_manifest,"health_endpoint":x.health_endpoint,"governance_compatible":x.governance_compatible,"provenance_verified":x.provenance_verified,"policy_profile":x.policy_profile,"capabilities":bool(x.capabilities)}
        missing=[k for k,v in checks.items() if not v]; score=round(sum(checks.values())/len(checks),4)
        trusted=score>=.83 and x.signed_manifest and x.governance_compatible and x.provenance_verified
        return TrustDecision(agent_id=x.agent_id,trust_score=score,status="trusted" if trusted else "untrusted",missing_requirements=missing,routable=trusted)
trusted_agent_engine=TrustedAgentEngine()
