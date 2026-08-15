from __future__ import annotations

import contextvars
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.governance_v10.schemas import AgentRunEventCreate, RunPolicyCheckRequest
from app.governance_v10.service import AgentGovernanceService


@dataclass(slots=True)
class GovernanceRuntime:
    session: AsyncSession
    user_id: uuid.UUID
    run_id: uuid.UUID
    conversation_id: uuid.UUID | None = None


_current_runtime: contextvars.ContextVar[GovernanceRuntime | None] = contextvars.ContextVar(
    "redpa_governance_runtime", default=None
)


def bind_runtime(runtime: GovernanceRuntime):
    return _current_runtime.set(runtime)


def reset_runtime(token) -> None:
    _current_runtime.reset(token)


def current_runtime() -> GovernanceRuntime | None:
    return _current_runtime.get()


async def record_runtime_event(
    *, event_type: str, stage: str | None = None, payload: dict[str, Any] | None = None
) -> None:
    runtime = current_runtime()
    if runtime is None:
        return
    await AgentGovernanceService().add_event(
        session=runtime.session,
        run_id=runtime.run_id,
        user_id=runtime.user_id,
        payload=AgentRunEventCreate(
            event_type=event_type,
            stage=stage,
            payload=payload or {},
        ),
    )


async def runtime_policy_check(
    *, action: str, arguments: dict[str, Any] | None = None,
    boundary: str = "tool", resource: str | None = None,
    request_content: str | None = None, approval_granted: bool = False,
):
    runtime = current_runtime()
    if runtime is None:
        return None
    return await AgentGovernanceService().policy_check(
        session=runtime.session,
        run_id=runtime.run_id,
        user_id=runtime.user_id,
        payload=RunPolicyCheckRequest(
            action=action,
            boundary=boundary,
            resource=resource,
            arguments=arguments or {},
            conversation_id=runtime.conversation_id,
            request_content=request_content,
            approval_granted=approval_granted,
            metadata={"integration": "v10_phase2"},
        ),
    )
