from __future__ import annotations
from dataclasses import dataclass
from .agent_runtime import AgentRuntimeRegistry
from .connectors import ConnectorRegistry
from .evaluation_platform import EvaluationPlatform
from .event_platform import EventPlatform
from .model_governance import ModelGovernanceService
from .policy_platform import PolicyPlatform
from .tool_platform import ToolPlatform
from .workflow_engine import WorkflowEngine
from .memory_platform import MemoryPlatform

@dataclass(slots=True)
class ControlCenter:
    models:ModelGovernanceService
    agents:AgentRuntimeRegistry
    tools:ToolPlatform
    workflows:WorkflowEngine
    memory:MemoryPlatform
    evaluations:EvaluationPlatform
    connectors:ConnectorRegistry
    policies:PolicyPlatform
    events:EventPlatform
    def overview(self)->dict[str,int]:
        return {"model_budgets":len(self.models.budgets.list()),"agents":len(self.agents.registry.list()),"tools":len(self.tools.registry.list()),"workflows":len(self.workflows.runs.list()),"memories":len(self.memory.items.list()),"evaluations":len(self.evaluations.runs.list()),"connectors":len(self.connectors.registry.list()),"policies":len(self.policies.rules.list()),"events":len(self.events.events.list()),"dead_letters":len(self.events.dlq.list())}
