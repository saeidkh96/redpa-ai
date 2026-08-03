from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query

from app.agent_memory.analytics import (
    AgentMemoryAnalyticsService,
)
from app.agent_memory.hooks import (
    AgentMemoryHooks,
)
from app.agent_memory.maintenance import (
    AgentMemoryMaintenanceService,
)


router = APIRouter(
    prefix="/memory/admin",
    tags=["Agent Memory Admin"],
)


@router.get("/analytics")
async def memory_analytics() -> dict:
    return await AgentMemoryAnalyticsService.overview()


@router.post("/summarize")
async def summarize_memories(
    agent_id: str,
    memory_ids: list[UUID],
    workflow_id: UUID | None = None,
    user_id: UUID | None = None,
    importance: float = Query(
        default=0.8,
        ge=0.0,
        le=1.0,
    ),
):
    return await AgentMemoryMaintenanceService.summarize(
        agent_id=agent_id,
        memory_ids=memory_ids,
        workflow_id=workflow_id,
        user_id=user_id,
        importance=importance,
    )


@router.post("/deduplicate")
async def deduplicate_memories(
    agent_id: str | None = None,
    user_id: UUID | None = None,
    workflow_id: UUID | None = None,
    similarity_threshold: float = Query(
        default=0.92,
        ge=0.0,
        le=1.0,
    ),
    limit: int = Query(
        default=500,
        ge=1,
        le=5000,
    ),
):
    return await AgentMemoryMaintenanceService.deduplicate(
        agent_id=agent_id,
        user_id=user_id,
        workflow_id=workflow_id,
        similarity_threshold=similarity_threshold,
        limit=limit,
    )


@router.post("/retention")
async def apply_memory_retention(
    max_age_days: int = Query(
        default=180,
        ge=1,
        le=3650,
    ),
    minimum_importance: float = Query(
        default=0.35,
        ge=0.0,
        le=1.0,
    ),
    limit: int = Query(
        default=1000,
        ge=1,
        le=10000,
    ),
):
    return await AgentMemoryMaintenanceService.apply_retention(
        max_age_days=max_age_days,
        minimum_importance=minimum_importance,
        limit=limit,
    )


@router.post("/inject/planner")
async def inject_planner_memory(
    prompt: str,
    user_id: UUID | None = None,
    workflow_id: UUID | None = None,
):
    return await AgentMemoryHooks.for_planner(
        prompt=prompt,
        user_id=user_id,
        workflow_id=workflow_id,
    )


@router.post("/inject/chat")
async def inject_chat_memory(
    prompt: str,
    user_id: UUID | None = None,
    workflow_id: UUID | None = None,
):
    return await AgentMemoryHooks.for_chat(
        prompt=prompt,
        user_id=user_id,
        workflow_id=workflow_id,
    )


@router.post("/inject/research")
async def inject_research_memory(
    prompt: str,
    user_id: UUID | None = None,
    workflow_id: UUID | None = None,
):
    return await AgentMemoryHooks.for_research(
        prompt=prompt,
        user_id=user_id,
        workflow_id=workflow_id,
    )


@router.post("/inject/specialist/{agent_id}")
async def inject_specialist_memory(
    agent_id: str,
    prompt: str,
    user_id: UUID | None = None,
    workflow_id: UUID | None = None,
):
    return await AgentMemoryHooks.for_specialist(
        prompt=prompt,
        specialist_agent_id=agent_id,
        user_id=user_id,
        workflow_id=workflow_id,
    )
