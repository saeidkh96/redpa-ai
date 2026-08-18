from app.self_healing.health_state import RuntimeHealthStatus

class AgentRejoinPolicy:
    @staticmethod
    def allowed(health) -> bool:
        return health.status == RuntimeHealthStatus.HEALTHY and health.consecutive_failures == 0

agent_rejoin_policy = AgentRejoinPolicy()
