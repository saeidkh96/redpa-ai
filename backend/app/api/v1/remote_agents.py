from __future__ import annotations

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Response,
    status,
)

from app.a2a_remote.client import (
    RemoteA2AError,
)
from app.a2a_remote.schemas import (
    RemoteAgentCardResponse,
    RemoteAgentListResponse,
    RemoteAgentRegistrationRequest,
    RemoteAgentSummary,
    RemoteDelegationRequest,
    RemoteDelegationResponse,
)
from app.a2a_remote.service import (
    RemoteAgentAlreadyRegisteredError,
    RemoteAgentNotFoundError,
    RemoteAgentService,
)


router = APIRouter(
    prefix="/agents/remotes",
    tags=["A2A Remote Agents"],
)


@router.post(
    "",
    response_model=RemoteAgentSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Register a remote A2A agent",
)
async def register_remote_agent(
    request: RemoteAgentRegistrationRequest,
) -> RemoteAgentSummary:
    try:
        return await RemoteAgentService.register(
            request,
        )
    except RemoteAgentAlreadyRegisteredError as exception:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(
                exception,
            ),
        ) from exception
    except (
        RemoteA2AError,
        ValueError,
    ) as exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(
                exception,
            ),
        ) from exception


@router.get(
    "",
    response_model=RemoteAgentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List remote A2A agents",
)
async def list_remote_agents() -> RemoteAgentListResponse:
    return await RemoteAgentService.list()


@router.get(
    "/{name}/card",
    response_model=RemoteAgentCardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a remote Agent Card",
)
async def get_remote_agent_card(
    name: str,
    refresh: bool = Query(
        default=False,
    ),
) -> RemoteAgentCardResponse:
    try:
        return await RemoteAgentService.get_card(
            name,
            refresh=refresh,
        )
    except RemoteAgentNotFoundError as exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                exception,
            ),
        ) from exception
    except RemoteA2AError as exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(
                exception,
            ),
        ) from exception


@router.post(
    "/{name}/delegate",
    response_model=RemoteDelegationResponse,
    status_code=status.HTTP_200_OK,
    summary="Delegate a task to a remote A2A agent",
)
async def delegate_to_remote_agent(
    name: str,
    request: RemoteDelegationRequest,
) -> RemoteDelegationResponse:
    try:
        return await RemoteAgentService.delegate(
            name,
            request,
        )
    except RemoteAgentNotFoundError as exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                exception,
            ),
        ) from exception
    except RemoteA2AError as exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(
                exception,
            ),
        ) from exception


@router.delete(
    "/{name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unregister a remote A2A agent",
)
async def unregister_remote_agent(
    name: str,
) -> Response:
    try:
        await RemoteAgentService.unregister(
            name,
        )
    except RemoteAgentNotFoundError as exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                exception,
            ),
        ) from exception

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
