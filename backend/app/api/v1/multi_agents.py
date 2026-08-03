from __future__ import annotations

from fastapi import (
    APIRouter,
    status,
)

from app.a2a_multi.schemas import (
    MultiAgentRequest,
    MultiAgentResponse,
)
from app.a2a_multi.service import (
    MultiAgentWorkflowService,
)


router = APIRouter(
    prefix="/agents/multi",
    tags=["A2A Multi-Agent"],
)


@router.post(
    "/delegate",
    response_model=MultiAgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute a multi-agent workflow",
)
async def delegate_multi_agent_workflow(
    request: MultiAgentRequest,
) -> MultiAgentResponse:
    return await MultiAgentWorkflowService.execute(
        request,
    )
