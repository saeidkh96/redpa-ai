from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum
from .common import Registry

class ConnectorType(StrEnum): REST="rest"; WEBHOOK="webhook"; GITHUB="github"; JIRA="jira"; SLACK="slack"; CONFLUENCE="confluence"; EMAIL="email"
@dataclass(slots=True)
class ConnectorDefinition:
    connector_id:str
    tenant_id:str
    type:ConnectorType
    enabled:bool=True
    scopes:tuple[str,...]=()
    config:dict[str,str]=field(default_factory=dict)

class ConnectorRegistry:
    def __init__(self)->None:self.registry:Registry[ConnectorDefinition]=Registry()
    def register(self,item:ConnectorDefinition)->ConnectorDefinition:return self.registry.put(item.connector_id,item)
    def tenant_connectors(self,tenant_id:str)->list[ConnectorDefinition]:return [x for x in self.registry.list() if x.tenant_id==tenant_id]
