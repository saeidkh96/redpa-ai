from dataclasses import dataclass
@dataclass(frozen=True, slots=True)
class Check: name:str; passed:bool
def validate(e):
 keys=["inventory","health_dependencies","backup_restore","secrets_iam","capacity","observability","resilience","risk_score","deployment_gate"]
 c=[Check(f"Stage {i+1} {k.replace('_',' ')}", bool(e.get(k))) for i,k in enumerate(keys)]
 c.append(Check("Stage 10 readiness gate", all(x.passed for x in c)))
 return c
