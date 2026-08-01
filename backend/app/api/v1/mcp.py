from __future__ import annotations

from fastapi import (
    APIRouter,
    HTTPException,
    Path,
    status,
)

from app.api.dependencies import CurrentUser
from app.mcp.exceptions import MCPClientError
from app.mcp.registry import MCPServerNotFoundError
from app.mcp.schemas import (
    MCPServerInfo,
    MCPToolCallRequest,
    MCPToolCallResult,
    MCPToolInfo,
)
from app.services.mcp_service import MCPService


router = APIRouter(
    prefix="/mcp",
    tags=["MCP"],
)


@router.get(
    "/servers",
    response_model=list[MCPServerInfo],
    status_code=status.HTTP_200_OK,
    summary="List configured MCP servers",
)
async def list_mcp_servers(
    current_user: CurrentUser,
) -> list[MCPServerInfo]:
    del current_user
    return MCPService.list_servers()


@router.get(
    "/servers/{server_name}/tools",
    response_model=list[MCPToolInfo],
    status_code=status.HTTP_200_OK,
    summary="Discover tools from an MCP server",
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
            detail=str(exception),
        ) from exception
    except MCPClientError as exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exception),
        ) from exception


@router.post(
    "/servers/{server_name}/tools/{tool_name}/call",
    response_model=MCPToolCallResult,
    status_code=status.HTTP_200_OK,
    summary="Call a remote MCP tool",
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
        )
    except MCPServerNotFoundError as exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exception),
        ) from exception
    except MCPClientError as exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exception),
        ) from exception
