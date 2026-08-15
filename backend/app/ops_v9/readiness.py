from app.ops_v9.schemas import ReleaseReadinessDecision, ReleaseReadinessRequest


class ReleaseReadinessEvaluator:
    @staticmethod
    def evaluate(payload: ReleaseReadinessRequest) -> ReleaseReadinessDecision:
        checks = {
            'availability': payload.availability >= payload.availability_target,
            'p95_latency': payload.p95_latency_ms <= payload.p95_latency_target_ms,
            'critical_incidents': payload.open_critical_incidents == 0,
            'security_gate': payload.security_gate_passed,
            'regression_gate': payload.regression_gate_passed,
        }
        reasons = [name for name, passed in checks.items() if not passed]
        return ReleaseReadinessDecision(
            decision='PROMOTE' if all(checks.values()) else 'HOLD',
            checks=checks,
            reasons=reasons,
        )
