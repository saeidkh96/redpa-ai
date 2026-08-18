from app.continuous_evaluation_v16.engine import continuous_evaluation_engine
from app.continuous_evaluation_v16.schemas import EvaluationInput
def test_v16_promote():
 r=continuous_evaluation_engine.decide(EvaluationInput(candidate="c",baseline_score=.8,candidate_score=.85)); assert r.rollout_allowed
def test_v16_hold_regression():
 r=continuous_evaluation_engine.decide(EvaluationInput(candidate="c",baseline_score=.8,candidate_score=.85,error_rate_delta=.1)); assert r.decision=="hold"
