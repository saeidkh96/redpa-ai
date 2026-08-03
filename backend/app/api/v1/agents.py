from __future__ import annotations

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    status,
)

from app.a2a.schemas import (
    AgentCard,
    AgentHealthResponse,
    AgentListResponse,
    CapabilityDiscoveryResponse,
)
from app.a2a.service import (
    AgentNotFoundError,
    AgentService,
)


router = APIRouter(
    prefix="/agents",
    tags=["A2A Agents"],
)


@router.get(
    "",
    response_model=AgentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List registered agents",
)
async def list_agents() -> AgentListResponse:
    return await AgentService.list_agents()


@router.get(
    "/health",
    response_model=AgentHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get agent registry health",
)
async def get_agent_health() -> AgentHealthResponse:
    return await AgentService.health()


@router.get(
    "/discover",
    response_model=CapabilityDiscoveryResponse,
    status_code=status.HTTP_200_OK,
    summary="Discover agents by capability",
)
async def discover_agents(
    query: str = Query(
        min_length=1,
        max_length=500,
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
    ),
) -> CapabilityDiscoveryResponse:
    return await AgentService.discover(
        query,
        limit=limit,
    )


@router.get(
    "/{agent_id}",
    response_model=AgentCard,
    status_code=status.HTTP_200_OK,
    summary="Get an agent card",
)
async def get_agent(
    agent_id: str,
) -> AgentCard:
    try:
        return await AgentService.get_agent(
            agent_id,
        )
    except AgentNotFoundError as exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                exception,
            ),
        ) from exception
