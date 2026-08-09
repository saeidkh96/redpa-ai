from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.dependencies import CurrentUser, DatabaseSession
from app.events.contracts import EventEnvelope
from app.schemas.events import (
    EventCreateRequest,
    EventFlushResponse,
    EventOutboxResponse,
)
from app.services.event_outbox_service import EventOutboxService
from app.services.event_publisher_service import event_publisher_service


router = APIRouter(
    prefix="/events",
    tags=["Events"],
)


@router.post(
    "",
    response_model=EventOutboxResponse,
)
async def create_event(
    request: EventCreateRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> EventOutboxResponse:
    event = EventEnvelope(
        tenant_id=request.tenant_id,
        event_type=request.event_type,
        aggregate_type=request.aggregate_type,
        aggregate_id=request.aggregate_id,
        payload=request.payload,
        correlation_id=request.correlation_id,
        causation_id=request.causation_id,
        metadata={
            **request.metadata,
            "created_by_user_id": str(current_user.id),
        },
    )

    row = await EventOutboxService.enqueue(
        session=session,
        event=event,
    )
    return EventOutboxResponse.model_validate(row)


@router.get(
    "",
    response_model=list[EventOutboxResponse],
)
async def list_events(
    current_user: CurrentUser,
    session: DatabaseSession,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[EventOutboxResponse]:
    del current_user

    rows = await EventOutboxService.recent(
        session=session,
        limit=limit,
    )
    return [
        EventOutboxResponse.model_validate(row)
        for row in rows
    ]


@router.post(
    "/flush",
    response_model=EventFlushResponse,
)
async def flush_events(
    current_user: CurrentUser,
    session: DatabaseSession,
    limit: int = Query(default=100, ge=1, le=500),
) -> EventFlushResponse:
    del current_user

    result = await event_publisher_service.flush(
        session=session,
        limit=limit,
    )

    return EventFlushResponse(
        inspected=result.inspected,
        published=result.published,
        failed=result.failed,
    )
