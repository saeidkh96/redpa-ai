from __future__ import annotations

from fastapi import (
    APIRouter,
    HTTPException,
    Path,
    Query,
    status,
)

from app.api.dependencies import CurrentUser
from app.schemas.unified_tool import (
    UnifiedToolCatalogResponse,
    UnifiedToolInfo,
)
from app.services.unified_tool_service import (
    UnifiedToolNotFoundError,
    UnifiedToolService,
)


router = APIRouter(
    prefix="/tools/catalog",
    tags=["Tools"],
)


@router.get(
    "",
    response_model=UnifiedToolCatalogResponse,
    status_code=status.HTTP_200_OK,
    summary="List the unified tool catalog",
    description=(
        "Return internal RedPA tools and tools discovered from "
        "enabled MCP servers."
    ),
)
async def list_unified_tools(
    current_user: CurrentUser,
    refresh: bool = Query(
        default=False,
        description=(
            "Refresh MCP discovery before returning the catalog."
        ),
    ),
) -> UnifiedToolCatalogResponse:
    del current_user

    return await UnifiedToolService.get_catalog(
        force_refresh=refresh,
    )


@router.post(
    "/refresh",
    response_model=UnifiedToolCatalogResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh the unified tool catalog",
)
async def refresh_unified_tools(
    current_user: CurrentUser,
) -> UnifiedToolCatalogResponse:
    del current_user

    return await UnifiedToolService.refresh_catalog()


@router.get(
    "/{qualified_name:path}",
    response_model=UnifiedToolInfo,
    status_code=status.HTTP_200_OK,
    summary="Get one unified tool",
)
async def get_unified_tool(
    current_user: CurrentUser,
    qualified_name: str = Path(
        min_length=1,
        max_length=400,
        examples=[
            "internal:calculator",
            "mcp:example-remote:search",
        ],
    ),
) -> UnifiedToolInfo:
    del current_user

    try:
        return await UnifiedToolService.get_tool(
            qualified_name=qualified_name,
        )

    except UnifiedToolNotFoundError as exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exception),
        ) from exception
