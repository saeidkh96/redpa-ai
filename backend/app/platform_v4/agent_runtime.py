from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum
from .common import Registry

class AgentStatus(StrEnum): ENABLED="enabled"; DISABLED="disabled"; DRAINING="draining"
@dataclass(slots=True)
class AgentDefinition:
    agent_id: str
    version: str
    capabilities: tuple[str, ...]
    endpoint: str | None = None
    status: AgentStatus = AgentStatus.ENABLED
    metadata: dict[str, str] = field(default_factory=dict)

class AgentRuntimeRegistry:
    def __init__(self) -> None: self.registry: Registry[AgentDefinition] = Registry()
    def register(self, item: AgentDefinition) -> AgentDefinition: return self.registry.put(f"{item.agent_id}:{item.version}", item)
    def discover(self, capability: str) -> list[AgentDefinition]: return [x for x in self.registry.list() if x.status==AgentStatus.ENABLED and capability in x.capabilities]
