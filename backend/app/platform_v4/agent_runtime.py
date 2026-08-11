from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from .common import Registry


class AgentStatus(StrEnum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    DRAINING = "draining"


@dataclass(slots=True)
class AgentDefinition:
    agent_id: str
    version: str
    capabilities: tuple[str, ...]
    endpoint: str | None = None
    status: AgentStatus = AgentStatus.ENABLED
    allowed_models: tuple[str, ...] = ()
    allowed_tools: tuple[str, ...] = ()
    memory_policy: str = "tenant_scoped"
    approval_policy: str = "risk_based"
    evaluation_policy: str = "production_default"
    timeout_seconds: float = 120.0
    max_retries: int = 2
    max_cost_usd: float | None = None
    max_concurrency: int = 8
    metadata: dict[str, str] = field(default_factory=dict)


class AgentRuntimeRegistry:
    def __init__(self) -> None:
        self.registry: Registry[AgentDefinition] = Registry()

    def register(self, item: AgentDefinition) -> AgentDefinition:
        if item.timeout_seconds <= 0 or item.max_retries < 0 or item.max_concurrency < 1:
            raise ValueError("Invalid runtime limits.")
        return self.registry.put(f"{item.agent_id}:{item.version}", item)

    def discover(self, capability: str) -> list[AgentDefinition]:
        return [x for x in self.registry.list() if x.status == AgentStatus.ENABLED and capability in x.capabilities]

    def latest(self, agent_id: str) -> AgentDefinition | None:
        candidates = [x for x in self.registry.list() if x.agent_id == agent_id and x.status == AgentStatus.ENABLED]
        return sorted(candidates, key=lambda x: x.version, reverse=True)[0] if candidates else None
