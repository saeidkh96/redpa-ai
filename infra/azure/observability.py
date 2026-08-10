from __future__ import annotations
from dataclasses import dataclass
import pulumi
from foundation import Foundation

@dataclass(frozen=True, slots=True)
class ObservabilityOutputs:
    log_analytics_workspace_name: pulumi.Output[str]
    log_analytics_workspace_id: pulumi.Output[str]

class Observability:
    def __init__(self, foundation: Foundation) -> None:
        self.outputs = ObservabilityOutputs(foundation.log_workspace.name, foundation.log_workspace.id)
