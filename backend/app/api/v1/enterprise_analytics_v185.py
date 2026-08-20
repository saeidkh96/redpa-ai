import csv,io
from fastapi import APIRouter,Response
from app.api.dependencies import CurrentUser,DatabaseSession
from app.control_plane_v183.repository import execution_run_repository
router=APIRouter(prefix="/analytics/v18.5",tags=["V18.5 Enterprise Analytics"])
@router.get("/power-bi")
async def power_bi_dataset(current_user:CurrentUser,session:DatabaseSession):
 rows=await execution_run_repository.list(session,current_user.id,500); return [{"run_id":str(r.id),"created_at":r.created_at.isoformat(),"primary_agent":r.primary_agent,"fallback_agent":r.fallback_agent,"status":r.status,"duration_ms":r.duration_ms,"evaluation_score":r.evaluation_score,"fallback_count":r.fallback_count,"trace_id":r.trace_id} for r in rows]
@router.get("/excel.csv")
async def excel_export(current_user:CurrentUser,session:DatabaseSession):
 data=await power_bi_dataset(current_user,session); out=io.StringIO(); fields=["run_id","created_at","primary_agent","fallback_agent","status","duration_ms","evaluation_score","fallback_count","trace_id"]; w=csv.DictWriter(out,fieldnames=fields); w.writeheader(); w.writerows(data); return Response(out.getvalue(),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=redpa-agent-runs.csv"})
@router.get("/kpis")
async def kpis(current_user:CurrentUser,session:DatabaseSession):
 rows=await execution_run_repository.list(session,current_user.id,500); n=len(rows); recovered=sum(r.fallback_count>0 and r.status.lower() in {"pass","success","completed"} for r in rows); return {"total_agent_runs":n,"recovery_rate":round(recovered/max(sum(r.fallback_count>0 for r in rows),1)*100,2),"policy_denials":sum(r.status.lower()=="blocked" for r in rows),"average_latency_ms":round(sum(r.duration_ms for r in rows)/n,2) if n else 0}
