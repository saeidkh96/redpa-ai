from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum
from .common import Registry, utcnow

class WorkflowStatus(StrEnum): RUNNING="running"; PAUSED="paused"; COMPLETED="completed"; FAILED="failed"; CANCELLED="cancelled"
@dataclass(slots=True)
class WorkflowRun:
    run_id: str
    workflow: str
    version: str
    status: WorkflowStatus=WorkflowStatus.RUNNING
    checkpoint: str | None=None
    attempts: int=0
    history: list[dict[str,str]]=field(default_factory=list)
    def transition(self,status:WorkflowStatus,reason:str)->None:
        self.status=status; self.history.append({"at":utcnow().isoformat(),"status":status.value,"reason":reason})

class WorkflowEngine:
    def __init__(self)->None: self.runs: Registry[WorkflowRun]=Registry()
    def start(self,run:WorkflowRun)->WorkflowRun: return self.runs.put(run.run_id,run)
    def checkpoint(self,run_id:str,value:str)->WorkflowRun:
        run=self.runs.get(run_id)
        if run is None: raise KeyError(run_id)
        run.checkpoint=value; return run
