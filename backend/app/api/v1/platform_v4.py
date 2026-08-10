from __future__ import annotations

import uuid
from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import CurrentUser, DatabaseSession
from app.platform_v4.agent_runtime import AgentDefinition
from app.platform_v4.bootstrap import control_center
from app.platform_v4.connectors import ConnectorDefinition, ConnectorType
from app.platform_v4.policy_platform import PolicyRule
from app.platform_v4.tool_platform import ToolDefinition
from app.models.event_outbox import EventOutbox
from app.security.rbac import Role
from app.schemas.platform_v4 import (
    EventDeliveryCreateRequest,
    EventDeliveryFailureRequest,
    EventDeliveryResponse,
    PlatformBudgetResponse,
    PlatformBudgetUpsertRequest,
    PlatformUsageResponse,
    WorkflowCheckpointCreateRequest,
    WorkflowCheckpointResponse,
    WorkflowDefinitionCreateRequest,
    WorkflowDefinitionResponse,
    WorkflowRunCreateRequest,
    WorkflowRunResponse,
    WorkflowTransitionRequest,
)
from app.services.platform_v4_event_service import (
    PlatformEventDeliveryNotFoundError,
    PlatformEventService,
)
from app.services.platform_v4_model_governance_service import PlatformModelGovernanceService
from app.services.platform_v4_workflow_service import (
    PlatformWorkflowNotFoundError,
    PlatformWorkflowService,
    PlatformWorkflowTransitionError,
)
from app.services.tenant_service import TenantMembershipNotFoundError, TenantService


router = APIRouter(prefix="/platform", tags=["Platform Control Plane v4"])


class AgentIn(BaseModel):
    agent_id: str
    version: str
    capabilities: list[str]
    endpoint: str | None = None


class ToolIn(BaseModel):
    name: str
    source: str
    risk: str = "low"
    required_roles: list[str] = []
    approval_required: bool = False
    sandbox_profile: str = "restricted"


class ConnectorIn(BaseModel):
    connector_id: str
    tenant_id: str
    type: ConnectorType
    scopes: list[str] = []
    config: dict[str, str] = {}


class PolicyIn(BaseModel):
    policy_id: str
    tenant_id: str
    version: int = 1
    action: str
    effect: str
    risk_levels: list[str] = []
    required_approvals: int = 0


async def _require_membership(
    *,
    session: DatabaseSession,
    tenant_id: uuid.UUID,
    current_user: CurrentUser,
):
    try:
        return await TenantService.get_membership(
            session=session,
            tenant_id=tenant_id,
            user_id=current_user.id,
        )
    except TenantMembershipNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


def _require_role(membership, allowed: set[Role]) -> None:
    if Role(membership.role) not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant role does not allow this platform mutation.",
        )


async def _require_delivery_access(*, session: DatabaseSession, delivery_id: uuid.UUID, current_user: CurrentUser, mutate: bool = False):
    try:
        delivery = await PlatformEventService.get_delivery(session=session, delivery_id=delivery_id)
    except PlatformEventDeliveryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if delivery.tenant_id is None:
        if not current_user.is_superuser:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform-level event access requires superuser.")
        return delivery
    membership = await _require_membership(session=session, tenant_id=delivery.tenant_id, current_user=current_user)
    if mutate:
        _require_role(membership, {Role.OWNER, Role.ADMIN, Role.OPERATOR})
    return delivery


@router.get("/overview")
async def overview(current_user: CurrentUser) -> dict[str, int]:
    del current_user
    return control_center.overview()


# ---------------------------------------------------------------------------
# Persistent model governance
# ---------------------------------------------------------------------------


@router.get("/model-governance/{tenant_id}", response_model=PlatformBudgetResponse)
async def get_budget(
    tenant_id: uuid.UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> PlatformBudgetResponse:
    await _require_membership(session=session, tenant_id=tenant_id, current_user=current_user)
    budget = await PlatformModelGovernanceService.ensure_budget(
        session=session,
        tenant_id=tenant_id,
        commit=True,
    )
    return PlatformBudgetResponse.model_validate(budget, from_attributes=True)


@router.put("/model-governance/{tenant_id}", response_model=PlatformBudgetResponse)
async def put_budget(
    tenant_id: uuid.UUID,
    body: PlatformBudgetUpsertRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> PlatformBudgetResponse:
    membership = await _require_membership(session=session, tenant_id=tenant_id, current_user=current_user)
    _require_role(membership, {Role.OWNER, Role.ADMIN})
    try:
        budget = await PlatformModelGovernanceService.upsert_budget(
            session=session,
            tenant_id=tenant_id,
            monthly_token_limit=body.monthly_token_limit,
            monthly_cost_limit_usd=body.monthly_cost_limit_usd,
            allowed_providers=body.allowed_providers,
            actor_id=current_user.id,
        )
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Budget update conflicted.") from exc
    return PlatformBudgetResponse.model_validate(budget, from_attributes=True)


@router.get("/model-governance/{tenant_id}/usage", response_model=list[PlatformUsageResponse])
async def usage_history(
    tenant_id: uuid.UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[PlatformUsageResponse]:
    await _require_membership(session=session, tenant_id=tenant_id, current_user=current_user)
    rows = await PlatformModelGovernanceService.recent_usage(
        session=session,
        tenant_id=tenant_id,
        limit=limit,
    )
    return [PlatformUsageResponse.model_validate(row, from_attributes=True) for row in rows]


# ---------------------------------------------------------------------------
# Persistent workflow control plane
# ---------------------------------------------------------------------------


@router.post("/workflows/{tenant_id}/definitions", response_model=WorkflowDefinitionResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow_definition(
    tenant_id: uuid.UUID,
    body: WorkflowDefinitionCreateRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> WorkflowDefinitionResponse:
    membership = await _require_membership(session=session, tenant_id=tenant_id, current_user=current_user)
    _require_role(membership, {Role.OWNER, Role.ADMIN})
    try:
        row = await PlatformWorkflowService.create_definition(
            session=session,
            tenant_id=tenant_id,
            name=body.name,
            version=body.version,
            definition=body.definition,
            created_by=current_user.id,
        )
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Workflow version already exists.") from exc
    return WorkflowDefinitionResponse.model_validate(row, from_attributes=True)


@router.get("/workflows/{tenant_id}/definitions", response_model=list[WorkflowDefinitionResponse])
async def list_workflow_definitions(
    tenant_id: uuid.UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[WorkflowDefinitionResponse]:
    await _require_membership(session=session, tenant_id=tenant_id, current_user=current_user)
    rows = await PlatformWorkflowService.list_definitions(session=session, tenant_id=tenant_id, limit=limit)
    return [WorkflowDefinitionResponse.model_validate(row, from_attributes=True) for row in rows]


@router.post("/workflows/{tenant_id}/runs", response_model=WorkflowRunResponse, status_code=status.HTTP_201_CREATED)
async def start_workflow_run(
    tenant_id: uuid.UUID,
    body: WorkflowRunCreateRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> WorkflowRunResponse:
    membership = await _require_membership(session=session, tenant_id=tenant_id, current_user=current_user)
    _require_role(membership, {Role.OWNER, Role.ADMIN, Role.OPERATOR})
    try:
        row = await PlatformWorkflowService.start_run(
            session=session,
            tenant_id=tenant_id,
            workflow_name=body.workflow_name,
            workflow_version=body.workflow_version,
            definition_id=body.definition_id,
            input_payload=body.input_payload,
            correlation_id=body.correlation_id,
            created_by=current_user.id,
        )
    except PlatformWorkflowNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return WorkflowRunResponse.model_validate(row, from_attributes=True)


@router.get("/workflows/{tenant_id}/runs", response_model=list[WorkflowRunResponse])
async def list_workflow_runs(
    tenant_id: uuid.UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
    run_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[WorkflowRunResponse]:
    await _require_membership(session=session, tenant_id=tenant_id, current_user=current_user)
    rows = await PlatformWorkflowService.list_runs(
        session=session,
        tenant_id=tenant_id,
        status=run_status,
        limit=limit,
    )
    return [WorkflowRunResponse.model_validate(row, from_attributes=True) for row in rows]


@router.post("/workflows/{tenant_id}/runs/{run_id}/checkpoints", response_model=WorkflowCheckpointResponse, status_code=status.HTTP_201_CREATED)
async def checkpoint_workflow(
    tenant_id: uuid.UUID,
    run_id: uuid.UUID,
    body: WorkflowCheckpointCreateRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> WorkflowCheckpointResponse:
    membership = await _require_membership(session=session, tenant_id=tenant_id, current_user=current_user)
    _require_role(membership, {Role.OWNER, Role.ADMIN, Role.OPERATOR})
    try:
        row = await PlatformWorkflowService.checkpoint(
            session=session,
            tenant_id=tenant_id,
            run_id=run_id,
            checkpoint_key=body.checkpoint_key,
            state=body.state,
            reason=body.reason,
        )
    except PlatformWorkflowNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PlatformWorkflowTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return WorkflowCheckpointResponse.model_validate(row, from_attributes=True)


@router.post("/workflows/{tenant_id}/runs/{run_id}/transition", response_model=WorkflowRunResponse)
async def transition_workflow(
    tenant_id: uuid.UUID,
    run_id: uuid.UUID,
    body: WorkflowTransitionRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> WorkflowRunResponse:
    membership = await _require_membership(session=session, tenant_id=tenant_id, current_user=current_user)
    _require_role(membership, {Role.OWNER, Role.ADMIN, Role.OPERATOR})
    try:
        row = await PlatformWorkflowService.transition(
            session=session,
            tenant_id=tenant_id,
            run_id=run_id,
            to_status=body.status,
            reason=body.reason,
            output_payload=body.output_payload,
            error=body.error,
        )
    except PlatformWorkflowNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PlatformWorkflowTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return WorkflowRunResponse.model_validate(row, from_attributes=True)


# ---------------------------------------------------------------------------
# Event delivery, retry, DLQ, and replay integrated with v3 outbox
# ---------------------------------------------------------------------------


@router.post("/events/deliveries", response_model=EventDeliveryResponse, status_code=status.HTTP_201_CREATED)
async def create_event_delivery(
    body: EventDeliveryCreateRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> EventDeliveryResponse:
    outbox = await session.get(EventOutbox, body.event_id)
    if outbox is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Outbox event not found: {body.event_id}")
    if outbox.tenant_id is None:
        if not current_user.is_superuser:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform-level event access requires superuser.")
    else:
        membership = await _require_membership(session=session, tenant_id=outbox.tenant_id, current_user=current_user)
        _require_role(membership, {Role.OWNER, Role.ADMIN, Role.OPERATOR})
    try:
        row = await PlatformEventService.create_delivery(
            session=session,
            event_id=body.event_id,
            consumer=body.consumer,
            max_attempts=body.max_attempts,
        )
    except PlatformEventDeliveryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return EventDeliveryResponse.model_validate(row, from_attributes=True)


@router.post("/events/deliveries/{delivery_id}/failed", response_model=EventDeliveryResponse)
async def fail_event_delivery(
    delivery_id: uuid.UUID,
    body: EventDeliveryFailureRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> EventDeliveryResponse:
    await _require_delivery_access(session=session, delivery_id=delivery_id, current_user=current_user, mutate=True)
    try:
        row = await PlatformEventService.mark_failed(
            session=session,
            delivery_id=delivery_id,
            error=body.error,
            base_delay_seconds=body.base_delay_seconds,
        )
    except PlatformEventDeliveryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return EventDeliveryResponse.model_validate(row, from_attributes=True)


@router.post("/events/deliveries/{delivery_id}/delivered", response_model=EventDeliveryResponse)
async def complete_event_delivery(
    delivery_id: uuid.UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> EventDeliveryResponse:
    await _require_delivery_access(session=session, delivery_id=delivery_id, current_user=current_user, mutate=True)
    try:
        row = await PlatformEventService.mark_delivered(session=session, delivery_id=delivery_id)
    except PlatformEventDeliveryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return EventDeliveryResponse.model_validate(row, from_attributes=True)


@router.get("/events/dead-letter", response_model=list[EventDeliveryResponse])
async def dead_letters(
    current_user: CurrentUser,
    session: DatabaseSession,
    tenant_id: uuid.UUID | None = None,
    consumer: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[EventDeliveryResponse]:
    if tenant_id is not None:
        await _require_membership(session=session, tenant_id=tenant_id, current_user=current_user)
    elif not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Specify a tenant_id or use a superuser account.")
    rows = await PlatformEventService.list_dead_letters(
        session=session,
        tenant_id=tenant_id,
        consumer=consumer,
        limit=limit,
    )
    return [EventDeliveryResponse.model_validate(row, from_attributes=True) for row in rows]


@router.post("/events/dead-letter/{delivery_id}/replay", response_model=EventDeliveryResponse)
async def replay_dead_letter(
    delivery_id: uuid.UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> EventDeliveryResponse:
    await _require_delivery_access(session=session, delivery_id=delivery_id, current_user=current_user, mutate=True)
    try:
        row = await PlatformEventService.replay(session=session, delivery_id=delivery_id)
    except PlatformEventDeliveryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return EventDeliveryResponse.model_validate(row, from_attributes=True)


# ---------------------------------------------------------------------------
# The remaining v4 domains stay on their additive in-memory foundation for now.
# ---------------------------------------------------------------------------


@router.post("/agents")
async def register_agent(body: AgentIn, current_user: CurrentUser):
    del current_user
    return asdict(control_center.agents.register(AgentDefinition(body.agent_id, body.version, tuple(body.capabilities), body.endpoint)))


@router.post("/tools")
async def register_tool(body: ToolIn, current_user: CurrentUser):
    del current_user
    return asdict(control_center.tools.register(ToolDefinition(body.name, body.source, body.risk, tuple(body.required_roles), body.approval_required, body.sandbox_profile)))


@router.post("/connectors")
async def register_connector(body: ConnectorIn, current_user: CurrentUser):
    del current_user
    return asdict(control_center.connectors.register(ConnectorDefinition(body.connector_id, body.tenant_id, body.type, True, tuple(body.scopes), body.config)))


@router.post("/policies")
async def publish_policy(body: PolicyIn, current_user: CurrentUser):
    del current_user
    return asdict(control_center.policies.publish(PolicyRule(body.policy_id, body.tenant_id, body.version, body.action, body.effect, tuple(body.risk_levels), body.required_approvals)))
