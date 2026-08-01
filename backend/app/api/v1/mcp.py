from fastapi import (
    APIRouter,
    HTTPException,
    Path,
    Query,
    status,
)

from app.api.dependencies import CurrentUser
from app.mcp.exceptions import MCPClientError
from app.mcp.naming import MCPQualifiedNameError
from app.mcp.permissions import (
    MCPApprovalRequiredError,
    MCPToolNotAllowedError,
)
from app.mcp.registry import MCPServerNotFoundError
from app.mcp.schemas import (
    MCPHealthResponse,
    MCPQualifiedToolCallRequest,
    MCPReloadResponse,
    MCPServerInfo,
    MCPToolCallRequest,
    MCPToolCallResult,
    MCPToolCatalogResponse,
    MCPToolInfo,
)
from app.services.mcp_service import (
    MCPService,
    MCPToolNotFoundError,
)


router = APIRouter(
    prefix="/mcp",
    tags=["MCP"],
)


@router.get("/servers", response_model=list[MCPServerInfo])
async def list_mcp_servers(
    current_user: CurrentUser,
) -> list[MCPServerInfo]:
    del current_user
    return MCPService.list_servers()


@router.post(
    "/servers/reload",
    response_model=MCPReloadResponse,
)
async def reload_mcp_servers(
    current_user: CurrentUser,
) -> MCPReloadResponse:
    del current_user
    return await MCPService.reload_servers()


@router.get(
    "/health",
    response_model=MCPHealthResponse,
)
async def get_mcp_health(
    current_user: CurrentUser,
) -> MCPHealthResponse:
    del current_user
    return await MCPService.health()


@router.get(
    "/tools",
    response_model=MCPToolCatalogResponse,
)
async def list_all_mcp_tools(
    current_user: CurrentUser,
    refresh: bool = Query(
        default=False,
    ),
) -> MCPToolCatalogResponse:
    del current_user
    return await MCPService.list_all_tools(
        force_refresh=refresh,
    )


@router.get(
    "/tools/{qualified_name:path}",
    response_model=MCPToolInfo,
)
async def get_mcp_tool(
    current_user: CurrentUser,
    qualified_name: str = Path(
        min_length=7,
        max_length=500,
    ),
) -> MCPToolInfo:
    del current_user

    try:
        return await MCPService.get_tool(
            qualified_name=qualified_name,
        )
    except (
        MCPQualifiedNameError,
        MCPToolNotFoundError,
    ) as exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                exception,
            ),
        ) from exception


@router.post(
    "/tools/execute",
    response_model=MCPToolCallResult,
)
async def execute_qualified_mcp_tool(
    request: MCPQualifiedToolCallRequest,
    current_user: CurrentUser,
) -> MCPToolCallResult:
    del current_user

    try:
        return await MCPService.call_qualified_tool(
            qualified_name=request.qualified_name,
            arguments=request.arguments,
            approval_granted=request.approval_granted,
        )
    except MCPApprovalRequiredError as exception:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(
                exception,
            ),
        ) from exception
    except MCPToolNotAllowedError as exception:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(
                exception,
            ),
        ) from exception
    except (
        MCPQualifiedNameError,
        MCPServerNotFoundError,
        MCPToolNotFoundError,
    ) as exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                exception,
            ),
        ) from exception
    except MCPClientError as exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(
                exception,
            ),
        ) from exception


@router.get(
    "/servers/{server_name}/tools",
    response_model=list[MCPToolInfo],
)
async def list_mcp_tools(
    current_user: CurrentUser,
    server_name: str = Path(
        min_length=1,
        max_length=100,
    ),
) -> list[MCPToolInfo]:
    del current_user

    try:
        return await MCPService.list_tools(
            server_name=server_name,
        )
    except MCPServerNotFoundError as exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                exception,
            ),
        ) from exception
    except MCPClientError as exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(
                exception,
            ),
        ) from exception


@router.post(
    "/servers/{server_name}/tools/{tool_name}/call",
    response_model=MCPToolCallResult,
)
async def call_mcp_tool(
    request: MCPToolCallRequest,
    current_user: CurrentUser,
    server_name: str = Path(
        min_length=1,
        max_length=100,
    ),
    tool_name: str = Path(
        min_length=1,
        max_length=200,
    ),
) -> MCPToolCallResult:
    del current_user

    try:
        return await MCPService.call_tool(
            server_name=server_name,
            tool_name=tool_name,
            arguments=request.arguments,
            approval_granted=request.approval_granted,
        )
    except MCPApprovalRequiredError as exception:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(
                exception,
            ),
        ) from exception
    except MCPToolNotAllowedError as exception:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(
                exception,
            ),
        ) from exception
    except (
        MCPServerNotFoundError,
        MCPToolNotFoundError,
    ) as exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                exception,
            ),
        ) from exception
    except MCPClientError as exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(
                exception,
            ),
        ) from exception
