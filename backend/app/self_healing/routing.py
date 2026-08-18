from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.a2a.registry import agent_registry
from app.a2a.schemas import AgentStatus
from app.a2a.service import AgentService


class CandidateHealth(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class RoutingCandidate:
    agent_id: str
    capability: str
    capability_score: float
    health: CandidateHealth
    routable: bool
    rank: int


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    query: str
    selected_agent_id: str | None
    candidates: tuple[RoutingCandidate, ...]
    reason: str


class HealthAwareAgentRouter:
    _HEALTH_PRIORITY = {
        CandidateHealth.HEALTHY: 0,
        CandidateHealth.DEGRADED: 1,
        CandidateHealth.UNKNOWN: 2,
        CandidateHealth.OFFLINE: 3,
    }

    @staticmethod
    def _map_status(status: AgentStatus) -> CandidateHealth:
        if status == AgentStatus.ACTIVE:
            return CandidateHealth.HEALTHY
        if status == AgentStatus.DEGRADED:
            return CandidateHealth.DEGRADED
        if status == AgentStatus.OFFLINE:
            return CandidateHealth.OFFLINE
        return CandidateHealth.UNKNOWN

    async def select(self, query: str, *, limit: int = 10, allow_degraded: bool = True) -> RoutingDecision:
        normalized_query = str(query or "").strip()
        if not normalized_query:
            return RoutingDecision("", None, (), "empty_query")

        await AgentService.ensure_initialized()
        discovery = await agent_registry.discover(normalized_query, limit=limit)
        if not discovery.matches:
            return RoutingDecision(normalized_query, None, (), "no_capability_match")

        strongest_by_agent = {}
        for match in discovery.matches:
            current = strongest_by_agent.get(match.agent_id)
            if current is None or match.score > current.score:
                strongest_by_agent[match.agent_id] = match

        candidates = []
        for match in strongest_by_agent.values():
            card = await agent_registry.get(match.agent_id)
            health = self._map_status(card.status)
            routable = health == CandidateHealth.HEALTHY or (allow_degraded and health == CandidateHealth.DEGRADED)
            candidates.append(RoutingCandidate(match.agent_id, match.capability_name, match.score, health, routable, 0))

        candidates.sort(key=lambda x: (not x.routable, self._HEALTH_PRIORITY[x.health], -x.capability_score, x.agent_id))
        ranked = tuple(RoutingCandidate(x.agent_id, x.capability, x.capability_score, x.health, x.routable, i) for i, x in enumerate(candidates, 1))
        selected = next((c for c in ranked if c.routable), None)
        reason = "no_healthy_candidate" if selected is None else ("healthy_capability_match" if selected.health == CandidateHealth.HEALTHY else "degraded_fallback")
        return RoutingDecision(normalized_query, selected.agent_id if selected else None, ranked, reason)


health_aware_agent_router = HealthAwareAgentRouter()
