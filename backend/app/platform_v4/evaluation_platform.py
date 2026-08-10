from __future__ import annotations
from dataclasses import dataclass, field
from statistics import mean
from .common import Registry

@dataclass(slots=True)
class EvaluationRun:
    run_id:str
    suite:str
    version:str
    scores:dict[str,float]=field(default_factory=dict)
    latency_ms:float=0
    cost_usd:float=0

class EvaluationPlatform:
    def __init__(self)->None: self.runs:Registry[EvaluationRun]=Registry()
    def record(self,run:EvaluationRun)->EvaluationRun: return self.runs.put(run.run_id,run)
    def aggregate(self,suite:str)->dict[str,float]:
        runs=[x for x in self.runs.list() if x.suite==suite]
        if not runs: return {"runs":0.0}
        keys=set().union(*(x.scores for x in runs))
        out={k:mean(x.scores[k] for x in runs if k in x.scores) for k in keys}
        out["runs"]=float(len(runs)); out["avg_latency_ms"]=mean(x.latency_ms for x in runs); out["total_cost_usd"]=sum(x.cost_usd for x in runs); return out
