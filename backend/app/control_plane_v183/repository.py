from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.control_plane_v183 import AgentExecutionRun
from .schemas import ExecutionRunCreate
class ExecutionRunRepository:
 async def create(self,session:AsyncSession,user_id,payload:ExecutionRunCreate):
  row=AgentExecutionRun(user_id=user_id,**payload.model_dump()); session.add(row); await session.commit(); await session.refresh(row); return row
 async def list(self,session:AsyncSession,user_id,limit:int=100):
  q=select(AgentExecutionRun).where(AgentExecutionRun.user_id==user_id).order_by(AgentExecutionRun.created_at.desc()).limit(limit); return list((await session.scalars(q)).all())
execution_run_repository=ExecutionRunRepository()
