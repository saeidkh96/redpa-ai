from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Response,
    status,
)

from app.agent_memory.repository import (
    AgentMemoryRepository,
    MemoryNotFoundError,
)
from app.agent_memory.schemas import (
    MemoryCreate,
    MemoryRecord,
    MemorySearchRequest,
    MemorySearchResult,
    MemoryUpdate,
    SharedMemoryContextRequest,
    SharedMemoryPublishRequest,
)
from app.agent_memory.service import (
    AgentMemoryService,
)


router = APIRouter(
    prefix="/memory",
    tags=["Agent Memory"],
)


@router.post(
    "",
    response_model=MemoryRecord,
    status_code=status.HTTP_201_CREATED,
)
async def create_memory(
    payload: MemoryCreate,
) -> MemoryRecord:
    return await AgentMemoryService.create(
        payload,
    )


@router.get(
    "",
    response_model=list[MemoryRecord],
)
async def list_memories(
    agent_id: str | None = None,
    user_id: UUID | None = None,
    workflow_id: UUID | None = None,
    scope: str | None = None,
    kind: str | None = None,
    active_only: bool = True,
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
) -> list[MemoryRecord]:
    return await AgentMemoryRepository.list(
        agent_id=agent_id,
        user_id=user_id,
        workflow_id=workflow_id,
        scope=scope,
        kind=kind,
        active_only=active_only,
        limit=limit,
    )


@router.get(
    "/{memory_id}",
    response_model=MemoryRecord,
)
async def get_memory(
    memory_id: UUID,
) -> MemoryRecord:
    try:
        return await AgentMemoryRepository.get(
            memory_id,
        )

    except MemoryNotFoundError as exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                exception,
            ),
        ) from exception


@router.patch(
    "/{memory_id}",
    response_model=MemoryRecord,
)
async def update_memory(
    memory_id: UUID,
    payload: MemoryUpdate,
) -> MemoryRecord:
    try:
        return await AgentMemoryService.update(
            memory_id,
            payload,
        )

    except MemoryNotFoundError as exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                exception,
            ),
        ) from exception


@router.delete(
    "/{memory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_memory(
    memory_id: UUID,
) -> Response:
    try:
        await AgentMemoryService.delete(
            memory_id,
        )

    except MemoryNotFoundError as exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                exception,
            ),
        ) from exception

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


@router.post(
    "/search",
    response_model=list[MemorySearchResult],
)
async def search_memory(
    payload: MemorySearchRequest,
) -> list[MemorySearchResult]:
    return await AgentMemoryService.search(
        payload,
    )


@router.post(
    "/shared/publish",
    response_model=MemoryRecord,
    status_code=status.HTTP_201_CREATED,
)
async def publish_shared_memory(
    payload: SharedMemoryPublishRequest,
) -> MemoryRecord:
    return await AgentMemoryService.publish_shared(
        payload,
    )


@router.post(
    "/shared/context",
    response_model=list[MemorySearchResult],
)
async def get_shared_memory_context(
    payload: SharedMemoryContextRequest,
) -> list[MemorySearchResult]:
    return await AgentMemoryService.shared_context(
        payload,
    )
