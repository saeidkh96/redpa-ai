from .schemas import EvaluationInput, EvaluationDecision
class ContinuousEvaluationEngine:
    def decide(self,x:EvaluationInput)->EvaluationDecision:
        d=round(x.candidate_score-x.baseline_score,4); reasons=[]
        if d < .02: reasons.append("insufficient_quality_gain")
        if x.error_rate_delta > .02: reasons.append("error_regression")
        if x.latency_delta > .20: reasons.append("latency_regression")
        if not x.safety_passed: reasons.append("safety_gate_failed")
        if not x.governance_passed: reasons.append("governance_gate_failed")
        allowed=not reasons
        return EvaluationDecision(decision="promote" if allowed else "hold",score_delta=d,reasons=reasons,rollout_allowed=allowed)
continuous_evaluation_engine=ContinuousEvaluationEngine()
