from __future__ import annotations
from dataclasses import dataclass, field
from .common import Registry

@dataclass(slots=True)
class ToolDefinition:
    name: str
    source: str
    risk: str = "low"
    required_roles: tuple[str, ...] = ()
    approval_required: bool = False
    sandbox_profile: str = "restricted"
    metadata: dict[str, str] = field(default_factory=dict)

class ToolPlatform:
    def __init__(self) -> None: self.registry: Registry[ToolDefinition] = Registry()
    def register(self, tool: ToolDefinition) -> ToolDefinition: return self.registry.put(tool.name, tool)
    def authorize(self, name: str, roles: set[str]) -> tuple[bool,str]:
        tool=self.registry.get(name)
        if not tool: return False,"tool_not_found"
        if tool.required_roles and not set(tool.required_roles).intersection(roles): return False,"role_denied"
        if tool.approval_required: return False,"human_approval_required"
        return True,"allowed"
