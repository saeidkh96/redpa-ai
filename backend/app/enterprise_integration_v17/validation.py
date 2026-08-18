from dataclasses import dataclass
@dataclass(frozen=True, slots=True)
class Check: name:str; passed:bool
def validate(e):
 keys=["registry","auth_scope","secret_handling","network_boundary","write_boundary","audit","rate_limit","risk_assessment","approval_gate"]
 c=[Check(f"Stage {i+1} {k.replace('_',' ')}",bool(e.get(k))) for i,k in enumerate(keys)]
 c.append(Check("Stage 10 integration gate",all(x.passed for x in c))); return c
