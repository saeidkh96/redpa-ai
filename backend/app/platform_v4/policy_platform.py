from __future__ import annotations
from dataclasses import dataclass, field
from .common import Registry

@dataclass(slots=True)
class PolicyRule:
    policy_id:str
    tenant_id:str
    version:int
    action:str
    effect:str
    risk_levels:tuple[str,...]=()
    required_approvals:int=0
    metadata:dict[str,str]=field(default_factory=dict)

class PolicyPlatform:
    def __init__(self)->None:self.rules:Registry[PolicyRule]=Registry()
    def publish(self,rule:PolicyRule)->PolicyRule:return self.rules.put(f"{rule.tenant_id}:{rule.policy_id}:{rule.version}",rule)
    def evaluate(self,tenant_id:str,action:str,risk:str)->dict[str,object]:
        matches=[x for x in self.rules.list() if x.tenant_id==tenant_id and x.action==action and (not x.risk_levels or risk in x.risk_levels)]
        if not matches:return {"effect":"deny","reason":"no_matching_policy","required_approvals":0}
        rule=max(matches,key=lambda x:x.version); return {"effect":rule.effect,"policy_id":rule.policy_id,"version":rule.version,"required_approvals":rule.required_approvals}
