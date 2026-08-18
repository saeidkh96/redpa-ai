from dataclasses import dataclass
@dataclass(frozen=True, slots=True)
class Check: name:str; passed:bool
def validate(e):
 keys=["identity","manifest_signature","provenance","capabilities","health","governance","policy_profile","trust_score","routing_boundary"]
 c=[Check(f"Stage {i+1} {k.replace('_',' ')}",bool(e.get(k))) for i,k in enumerate(keys)]
 c.append(Check("Stage 10 trusted-agent gate",all(x.passed for x in c))); return c
