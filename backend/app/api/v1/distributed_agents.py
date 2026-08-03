from __future__ import annotations

from fastapi import APIRouter, status

from app.distributed_multi.schemas import (
    DistributedWorkflowRequest,
    DistributedWorkflowResponse,
)
from app.distributed_multi.service import (
    DistributedMultiAgentService,
)


router = APIRouter(
    prefix="/agents/distributed",
    tags=["Distributed Agents"],
)


@router.post(
    "/execute",
    response_model=DistributedWorkflowResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute a distributed specialist workflow",
)
async def execute_distributed_workflow(
    request: DistributedWorkflowRequest,
) -> DistributedWorkflowResponse:
    return await DistributedMultiAgentService.execute(
        request,
    )
