from pydantic import BaseModel, Field
class EvaluationInput(BaseModel):
    candidate: str = Field(min_length=1,max_length=150)
    baseline_score: float = Field(ge=0,le=1)
    candidate_score: float = Field(ge=0,le=1)
    error_rate_delta: float = Field(default=0,ge=-1,le=1)
    latency_delta: float = Field(default=0,ge=-1,le=10)
    safety_passed: bool = True
    governance_passed: bool = True
class EvaluationDecision(BaseModel):
    decision:str; score_delta:float; reasons:list[str]; rollout_allowed:bool
