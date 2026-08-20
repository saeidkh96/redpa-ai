from fastapi import APIRouter, Query
from app.api.dependencies import CurrentUser, DatabaseSession
from app.control_plane_v183.repository import execution_run_repository
from app.control_plane_v183.schemas import ExecutionRunCreate,ExecutionRunOut,RunSummary
router=APIRouter(prefix="/control-plane/v18.3",tags=["V18.3 Control Plane"])
@router.post("/runs",response_model=ExecutionRunOut)
async def create_run(payload:ExecutionRunCreate,current_user:CurrentUser,session:DatabaseSession): return await execution_run_repository.create(session,current_user.id,payload)
@router.get("/runs",response_model=list[ExecutionRunOut])
async def list_runs(current_user:CurrentUser,session:DatabaseSession,limit:int=Query(100,ge=1,le=500)): return await execution_run_repository.list(session,current_user.id,limit)
@router.get("/summary",response_model=RunSummary)
async def summary(current_user:CurrentUser,session:DatabaseSession):
 rows=await execution_run_repository.list(session,current_user.id,500); n=len(rows); ok=sum(r.status.lower() in {"pass","passed","success","completed"} for r in rows); fail=n-ok; fb=sum(r.fallback_count>0 for r in rows); ds=[r.duration_ms for r in rows]; es=[r.evaluation_score for r in rows if r.evaluation_score is not None]
 return RunSummary(total_runs=n,successful_runs=ok,failed_runs=fail,fallback_runs=fb,success_rate=round(ok/n*100,2) if n else 0,fallback_rate=round(fb/n*100,2) if n else 0,average_duration_ms=round(sum(ds)/len(ds),2) if ds else 0,average_evaluation_score=round(sum(es)/len(es),4) if es else None)
