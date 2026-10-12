from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.dependencies import CurrentUser
from app.clients.n8n_client import N8NClient, N8NError


router = APIRouter(
    prefix="/automations",
    tags=["Automations"],
)


class AutomationRequest(BaseModel):
    workflow: str = Field(min_length=1, max_length=100)
    payload: dict[str, Any] = Field(default_factory=dict)


@router.post("/execute")
async def execute_automation(
    request: AutomationRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    # Authentication is required.
    # Workflow-specific permissions are not implemented yet.
    del current_user

    try:
        result = await N8NClient().execute(
            workflow=request.workflow,
            payload=request.payload,
        )
    except N8NError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    return {
        "workflow": request.workflow,
        "result": result,
    }
