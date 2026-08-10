from __future__ import annotations
from dataclasses import dataclass
from .common import Registry, utcnow

@dataclass(slots=True)
class MemoryPolicy:
    tenant_id: str
    retention_days: int=30
    max_items_per_agent: int=10000
    allow_shared_memory: bool=False
    redact_sensitive: bool=True

@dataclass(slots=True)
class MemoryItem:
    memory_id: str
    tenant_id: str
    agent_id: str
    scope: str
    content: str
    created_at: str

class MemoryPlatform:
    def __init__(self)->None: self.policies:Registry[MemoryPolicy]=Registry(); self.items:Registry[MemoryItem]=Registry()
    def add(self,item:MemoryItem)->MemoryItem:
        if item.scope=="shared":
            p=self.policies.get(item.tenant_id)
            if not p or not p.allow_shared_memory: raise PermissionError("shared_memory_disabled")
        return self.items.put(item.memory_id,item)
    def for_agent(self,tenant_id:str,agent_id:str)->list[MemoryItem]: return [x for x in self.items.list() if x.tenant_id==tenant_id and x.agent_id==agent_id]
