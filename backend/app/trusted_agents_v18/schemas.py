from pydantic import BaseModel, Field
class TrustedAgentInput(BaseModel):
    agent_id:str=Field(min_length=1,max_length=150)
    version:str=Field(min_length=1,max_length=80)
    capabilities:list[str]=Field(default_factory=list)
    signed_manifest:bool=False
    health_endpoint:bool=False
    governance_compatible:bool=True
    provenance_verified:bool=False
    policy_profile:bool=False
class TrustDecision(BaseModel):
    agent_id:str; trust_score:float; status:str; missing_requirements:list[str]; routable:bool
