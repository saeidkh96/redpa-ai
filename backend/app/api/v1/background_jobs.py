from __future__ import annotations
from fastapi import APIRouter, Query, status
from app.background_jobs.repository import BackgroundJobRepository
from app.background_jobs.schemas import BackgroundJobCreate, BackgroundJobRecord

router = APIRouter(prefix="/jobs", tags=["Background Jobs"])

@router.post("", response_model=BackgroundJobRecord, status_code=status.HTTP_201_CREATED)
async def enqueue_job(payload: BackgroundJobCreate):
    return await BackgroundJobRepository.enqueue(payload)

@router.get("", response_model=list[BackgroundJobRecord])
async def list_jobs(
    job_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
):
    return await BackgroundJobRepository.list(job_status, limit)
