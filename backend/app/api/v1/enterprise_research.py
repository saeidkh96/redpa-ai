from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    Query,
    status,
)

from app.research_workspace.repository import (
    EnterpriseResearchRepository,
    ResearchRunNotFoundError,
)
from app.research_workspace.schemas import (
    EnterpriseResearchRequest,
    EnterpriseResearchRun,
    EnterpriseResearchRunDetail,
    EnterpriseResearchRunList,
)
from app.research_workspace.service import (
    EnterpriseResearchService,
)


router = APIRouter(
    prefix="/research",
    tags=["V7 Enterprise Research"],
)


@router.post(
    "/runs",
    response_model=EnterpriseResearchRunDetail,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start a persisted enterprise research run",
)
async def start_enterprise_research(
    payload: EnterpriseResearchRequest,
    background_tasks: BackgroundTasks,
) -> EnterpriseResearchRunDetail:
    run_id = await EnterpriseResearchService.create(payload)
    background_tasks.add_task(
        EnterpriseResearchService.execute,
        run_id,
    )
    return await EnterpriseResearchRepository.get_run(run_id)


@router.get(
    "/runs",
    response_model=EnterpriseResearchRunList,
    summary="List enterprise research runs",
)
async def list_enterprise_research_runs(
    limit: int = Query(default=50, ge=1, le=200),
) -> EnterpriseResearchRunList:
    items = await EnterpriseResearchRepository.list_runs(
        limit=limit,
    )
    return EnterpriseResearchRunList(
        items=items,
        total=len(items),
    )


@router.get(
    "/runs/{run_id}",
    response_model=EnterpriseResearchRunDetail,
    summary="Get a research run with its live execution timeline",
)
async def get_enterprise_research_run(
    run_id: UUID,
) -> EnterpriseResearchRunDetail:
    try:
        return await EnterpriseResearchRepository.get_run(run_id)
    except ResearchRunNotFoundError as exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exception),
        ) from exception
