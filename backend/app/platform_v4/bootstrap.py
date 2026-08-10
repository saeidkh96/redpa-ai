from .agent_runtime import AgentRuntimeRegistry
from .connectors import ConnectorRegistry
from .control_center import ControlCenter
from .evaluation_platform import EvaluationPlatform
from .event_platform import EventPlatform
from .memory_platform import MemoryPlatform
from .model_governance import ModelGovernanceService
from .policy_platform import PolicyPlatform
from .tool_platform import ToolPlatform
from .workflow_engine import WorkflowEngine

control_center=ControlCenter(models=ModelGovernanceService(),agents=AgentRuntimeRegistry(),tools=ToolPlatform(),workflows=WorkflowEngine(),memory=MemoryPlatform(),evaluations=EvaluationPlatform(),connectors=ConnectorRegistry(),policies=PolicyPlatform(),events=EventPlatform())
