from __future__ import annotations

from fastapi import (
    APIRouter,
    HTTPException,
    Path,
    status,
)

from app.api.dependencies import CurrentUser
from app.schemas.tool import (
    ToolDiscoveryListResponse,
    ToolDiscoveryResponse,
)
from app.services.tool_service import ToolService
from app.tools.registry import ToolNotFoundError


router = APIRouter(
    prefix="/tools",
    tags=["Tools"],
)


@router.get(
    "",
    response_model=ToolDiscoveryListResponse,
    status_code=status.HTTP_200_OK,
    summary="List registered tools",
    description=(
        "Return metadata for every tool currently registered "
        "in the RedPA tool runtime."
    ),
)
async def list_registered_tools(
    current_user: CurrentUser,
) -> ToolDiscoveryListResponse:
    del current_user

    tools = ToolService.list_tools()

    items = [
        ToolDiscoveryResponse.model_validate(
            tool,
        )
        for tool in tools
    ]

    items.sort(
        key=lambda item: item.name.casefold(),
    )

    return ToolDiscoveryListResponse(
        items=items,
        total=len(items),
    )


@router.get(
    "/{tool_name}",
    response_model=ToolDiscoveryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get registered tool metadata",
    description=(
        "Return metadata for one registered RedPA tool."
    ),
)
async def get_registered_tool(
    current_user: CurrentUser,
    tool_name: str = Path(
        min_length=1,
        max_length=100,
        description=(
            "Case-insensitive registered tool name."
        ),
        examples=[
            "calculator",
            "datetime",
        ],
    ),
) -> ToolDiscoveryResponse:
    del current_user

    try:
        tool_metadata = ToolService.get_tool_metadata(
            tool_name=tool_name,
        )

    except ToolNotFoundError as exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exception),
        ) from exception

    return ToolDiscoveryResponse.model_validate(
        tool_metadata,
        from_attributes=True,
    )
