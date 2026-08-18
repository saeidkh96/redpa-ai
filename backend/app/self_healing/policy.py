from app.self_healing.schemas import FailoverRequest

class SelfHealingPolicy:
    @staticmethod
    def evaluate(request: FailoverRequest, selected_agent_id: str | None) -> tuple[str, str, bool, str]:
        if selected_agent_id is None:
            return "BLOCKED", "HIGH", False, "No routable replacement agent is available."
        high_risk = bool(request.context.get("destructive") or request.context.get("write_access") or request.context.get("handles_secrets"))
        if high_risk and not request.approval_granted:
            return "REVIEW", "HIGH", False, "High-risk failover requires explicit human approval."
        return ("REVIEW" if high_risk else "AUTO"), ("HIGH" if high_risk else "LOW"), True, "Failover may execute."

self_healing_policy = SelfHealingPolicy()
