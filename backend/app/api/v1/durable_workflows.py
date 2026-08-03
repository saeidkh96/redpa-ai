from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    status,
)

from app.distributed_durable.repository import (
    DurableWorkflowNotFoundError,
    DurableWorkflowRepository,
)
from app.distributed_durable.schemas import (
    DurableWorkflowCreate,
    DurableWorkflowExecutionResponse,
    DurableWorkflowRecord,
    DurableWorkflowResume,
)
from app.distributed_durable.service import (
    DurableDistributedWorkflowService,
)


router = APIRouter(
    prefix="/agents/distributed/durable",
    tags=["Durable Distributed Workflows"],
)


@router.post(
    "",
    response_model=DurableWorkflowExecutionResponse,
    status_code=status.HTTP_200_OK,
)
async def create_durable_workflow(
    payload: DurableWorkflowCreate,
) -> DurableWorkflowExecutionResponse:
    return await (
        DurableDistributedWorkflowService
        .create_and_execute(
            payload,
        )
    )


@router.get(
    "",
    response_model=list[DurableWorkflowRecord],
)
async def list_durable_workflows(
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
) -> list[DurableWorkflowRecord]:
    return await DurableWorkflowRepository.list_workflows(
        limit=limit,
    )


@router.get(
    "/{workflow_id}",
    response_model=DurableWorkflowRecord,
)
async def get_durable_workflow(
    workflow_id: UUID,
) -> DurableWorkflowRecord:
    try:
        return await DurableWorkflowRepository.get_workflow(
            workflow_id,
        )

    except DurableWorkflowNotFoundError as exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                exception,
            ),
        ) from exception


@router.post(
    "/{workflow_id}/resume",
    response_model=DurableWorkflowExecutionResponse,
)
async def resume_durable_workflow(
    workflow_id: UUID,
    payload: DurableWorkflowResume,
) -> DurableWorkflowExecutionResponse:
    try:
        return await (
            DurableDistributedWorkflowService.resume(
                workflow_id,
                payload,
            )
        )

    except DurableWorkflowNotFoundError as exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(
                exception,
            ),
        ) from exception
