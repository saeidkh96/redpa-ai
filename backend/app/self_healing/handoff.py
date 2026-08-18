from __future__ import annotations
from copy import deepcopy
from app.self_healing.schemas import FailoverRequest

class ContextHandoffService:
    @staticmethod
    def build(request: FailoverRequest, *, target_agent_id: str, trace_id: str | None = None) -> dict:
        context = deepcopy(request.context)
        return {
            "source_agent_id": request.failed_agent_id,
            "target_agent_id": target_agent_id,
            "task": request.task,
            "workflow_id": request.workflow_id,
            "run_id": str(request.run_id) if request.run_id else None,
            "trace_id": trace_id,
            "context": context,
        }

context_handoff_service = ContextHandoffService()
