from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
class ExecutionRunCreate(BaseModel):
    primary_agent:str=Field(min_length=1,max_length=120); fallback_agent:str|None=None; status:str="completed"; duration_ms:float=0; evaluation_score:float|None=None; fallback_count:int=0; trace_id:str|None=None; evidence:dict=Field(default_factory=dict)
class ExecutionRunOut(ExecutionRunCreate):
    id:UUID; source:str; created_at:datetime
    model_config={"from_attributes":True}
class RunSummary(BaseModel):
    total_runs:int; successful_runs:int; failed_runs:int; fallback_runs:int; success_rate:float; fallback_rate:float; average_duration_ms:float; average_evaluation_score:float|None
