from dataclasses import dataclass
@dataclass(frozen=True, slots=True)
class Check: name:str; passed:bool
def validate(e):
 keys=["dataset","baseline","candidate","quality_eval","safety_eval","regression","shadow","rollout_decision","rollback"]
 c=[Check(f"Stage {i+1} {k.replace('_',' ')}",bool(e.get(k))) for i,k in enumerate(keys)]
 c.append(Check("Stage 10 continuous evaluation gate",all(x.passed for x in c))); return c
