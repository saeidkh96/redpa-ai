from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.ops_v9.schemas import RemediationRequest
from app.ops_v9.service import OpsService


def _incident(*, status: str = "diagnosed"):
    return SimpleNamespace(
        id=uuid4(),
        service="redpa-research-agent",
        summary="V11 production validation",
        severity="warning",
        source="production-validation",
        status=status,
        diagnosis={"recommendation": "restart_container"},
        metadata={},
        resolved_at=None,
    )


def _action(
    *,
    incident_id,
    status: str = "approved",
    duplicate_detected: bool = False,
):
    return SimpleNamespace(
        id=uuid4(),
        incident_id=incident_id,
        action="restart_container",
        target="redpa-research-agent",
        status=status,
        approved=True,
        reason="V11 production validation",
        result={},
        error=None,
        idempotency_key="v11-test-key",
        duplicate_detected=duplicate_detected,
    )


def _policy(*, executable: bool = True):
    return SimpleNamespace(
        executable=executable,
        decision="ALLOW" if executable else "REVIEW",
        reason="test policy",
    )


@pytest.mark.asyncio
async def test_stage6_verification_timeout_fails_closed():
    """
    Stage 6:
    Restart succeeds but recovery verification fails.

    The system must fail closed:
      - action failed
      - incident failed
      - governed run finalized as failed
      - ops.recovery_failed emitted
      - incident never resolved
    """

    incident = _incident()
    action = _action(incident_id=incident.id)

    failed_incident = _incident(status="failed")
    failed_incident.id = incident.id

    finished_action = _action(
        incident_id=incident.id,
        status="failed",
    )

    events: list[str] = []

    async def capture_event(**kwargs):
        events.append(kwargs["event_type"])
        return SimpleNamespace()

    async def set_status(incident_id, status):
        assert incident_id == incident.id

        if status == "mitigating":
            mitigating = _incident(status="mitigating")
            mitigating.id = incident.id
            return mitigating

        if status == "failed":
            return failed_incident

        raise AssertionError(
            f"Unexpected incident status transition: {status}"
        )

    with (
        patch(
            "app.ops_v9.service.OpsRepository.get_incident",
            new=AsyncMock(return_value=incident),
        ),
        patch(
            "app.ops_v9.service.OpsRepository.create_action",
            new=AsyncMock(return_value=action),
        ),
        patch(
            "app.ops_v9.service.OpsRepository.set_incident_status",
            new=AsyncMock(side_effect=set_status),
        ) as set_status_mock,
        patch(
            "app.ops_v9.service.OpsRepository.finish_action",
            new=AsyncMock(return_value=finished_action),
        ) as finish_action_mock,
        patch(
            "app.ops_v9.service.OpsGovernanceBridge.remediation_policy",
            new=AsyncMock(return_value=_policy(executable=True)),
        ),
        patch(
            "app.ops_v9.service.OpsGovernanceBridge.event",
            new=AsyncMock(side_effect=capture_event),
        ),
        patch(
            "app.ops_v9.service.OpsGovernanceBridge.resume_after_approval",
            new=AsyncMock(),
        ),
        patch(
            "app.ops_v9.service.OpsGovernanceBridge.finish",
            new=AsyncMock(),
        ) as governance_finish_mock,
        patch(
            "app.ops_v9.service.OpsAgentClient.restart",
            new=AsyncMock(
                return_value={
                    "status": "completed",
                    "action": "restart_container",
                    "container": incident.service,
                    "state": "running",
                }
            ),
        ),
        patch(
            "app.ops_v9.service.OpsAgentClient.wait_until_healthy",
            new=AsyncMock(
                side_effect=RuntimeError(
                    "Recovery verification timed out"
                )
            ),
        ),
    ):
        result = await OpsService.remediate_governed(
            incident.id,
            RemediationRequest(
                action="restart_container",
                reason="Stage 6 controlled verification failure.",
                approved=True,
                idempotency_key="stage6-test",
            ),
            session=SimpleNamespace(),
            user_id=uuid4(),
            run_id=uuid4(),
        )

    assert result.status == "failed"

    statuses = [
        call.args[1]
        for call in set_status_mock.await_args_list
    ]

    assert "mitigating" in statuses
    assert "failed" in statuses
    assert "resolved" not in statuses

    assert "ops.recovery_failed" in events
    assert "ops.recovery_verified" not in events

    finish_action_mock.assert_awaited_once()
    assert (
        finish_action_mock.await_args.kwargs["status"]
        == "failed"
    )

    governance_finish_mock.assert_awaited_once()
    assert (
        governance_finish_mock.await_args.kwargs["success"]
        is False
    )


@pytest.mark.asyncio
async def test_stage7_approval_and_resume_are_explicitly_audited():
    """
    Stage 7:
    Approved remediation must explicitly audit approval and resume
    before destructive execution.
    """

    incident = _incident()
    action = _action(incident_id=incident.id)

    resolved_incident = _incident(status="resolved")
    resolved_incident.id = incident.id

    finished_action = _action(
        incident_id=incident.id,
        status="completed",
    )

    timeline: list[str] = []

    async def capture_event(**kwargs):
        timeline.append(kwargs["event_type"])
        return SimpleNamespace()

    async def capture_resume(**kwargs):
        timeline.append("bridge.resume_after_approval")
        return SimpleNamespace()

    async def capture_restart(*args, **kwargs):
        timeline.append("destructive.restart")
        return {
            "status": "completed",
            "action": "restart_container",
            "container": incident.service,
            "state": "running",
        }

    async def set_status(incident_id, status):
        if status == "mitigating":
            mitigating = _incident(status="mitigating")
            mitigating.id = incident.id
            return mitigating

        if status == "resolved":
            return resolved_incident

        raise AssertionError(
            f"Unexpected incident status: {status}"
        )

    with (
        patch(
            "app.ops_v9.service.OpsRepository.get_incident",
            new=AsyncMock(return_value=incident),
        ),
        patch(
            "app.ops_v9.service.OpsRepository.create_action",
            new=AsyncMock(return_value=action),
        ),
        patch(
            "app.ops_v9.service.OpsRepository.set_incident_status",
            new=AsyncMock(side_effect=set_status),
        ),
        patch(
            "app.ops_v9.service.OpsRepository.finish_action",
            new=AsyncMock(return_value=finished_action),
        ),
        patch(
            "app.ops_v9.service.OpsGovernanceBridge.remediation_policy",
            new=AsyncMock(return_value=_policy(executable=True)),
        ),
        patch(
            "app.ops_v9.service.OpsGovernanceBridge.event",
            new=AsyncMock(side_effect=capture_event),
        ),
        patch(
            "app.ops_v9.service.OpsGovernanceBridge.resume_after_approval",
            new=AsyncMock(side_effect=capture_resume),
        ),
        patch(
            "app.ops_v9.service.OpsGovernanceBridge.finish",
            new=AsyncMock(),
        ),
        patch(
            "app.ops_v9.service.OpsAgentClient.restart",
            new=AsyncMock(side_effect=capture_restart),
        ),
        patch(
            "app.ops_v9.service.OpsAgentClient.wait_until_healthy",
            new=AsyncMock(
                return_value={
                    "container": incident.service,
                    "state": "running",
                    "health": "healthy",
                }
            ),
        ),
    ):
        result = await OpsService.remediate_governed(
            incident.id,
            RemediationRequest(
                action="restart_container",
                reason="Stage 7 explicit approval audit validation.",
                approved=True,
                idempotency_key="stage7-test",
            ),
            session=SimpleNamespace(),
            user_id=uuid4(),
            run_id=uuid4(),
        )

    assert result.status == "completed"

    assert "human.approval_granted" in timeline
    assert "bridge.resume_after_approval" in timeline
    assert "run.resumed" in timeline
    assert "ops.remediation_started" in timeline
    assert "destructive.restart" in timeline
    assert "ops.recovery_verified" in timeline

    approval_index = timeline.index(
        "human.approval_granted"
    )
    bridge_resume_index = timeline.index(
        "bridge.resume_after_approval"
    )
    resumed_event_index = timeline.index(
        "run.resumed"
    )
    remediation_index = timeline.index(
        "ops.remediation_started"
    )
    restart_index = timeline.index(
        "destructive.restart"
    )
    verified_index = timeline.index(
        "ops.recovery_verified"
    )

    assert approval_index < bridge_resume_index
    assert bridge_resume_index < resumed_event_index
    assert resumed_event_index < remediation_index
    assert remediation_index < restart_index
    assert restart_index < verified_index


@pytest.mark.asyncio
async def test_stage8_duplicate_approved_request_executes_restart_once():
    """
    Stage 8:
    A duplicate idempotency key must return the persisted result
    without repeating the destructive restart.
    """

    incident = _incident()

    first_action = _action(
        incident_id=incident.id,
        duplicate_detected=False,
    )

    duplicate_action = _action(
        incident_id=incident.id,
        status="completed",
        duplicate_detected=True,
    )
    duplicate_action.id = first_action.id
    duplicate_action.result = {
        "state": "running",
        "health": "healthy",
    }

    completed_action = _action(
        incident_id=incident.id,
        status="completed",
    )
    completed_action.id = first_action.id
    completed_action.result = {
        "state": "running",
        "health": "healthy",
    }

    resolved_incident = _incident(status="resolved")
    resolved_incident.id = incident.id

    create_action_mock = AsyncMock(
        side_effect=[
            first_action,
            duplicate_action,
        ]
    )

    restart_mock = AsyncMock(
        return_value={
            "status": "completed",
            "action": "restart_container",
            "container": incident.service,
            "state": "running",
        }
    )

    async def set_status(incident_id, status):
        obj = _incident(status=status)
        obj.id = incident.id
        return obj

    with (
        patch(
            "app.ops_v9.service.OpsRepository.get_incident",
            new=AsyncMock(return_value=incident),
        ),
        patch(
            "app.ops_v9.service.OpsRepository.create_action",
            new=create_action_mock,
        ),
        patch(
            "app.ops_v9.service.OpsRepository.set_incident_status",
            new=AsyncMock(side_effect=set_status),
        ),
        patch(
            "app.ops_v9.service.OpsRepository.finish_action",
            new=AsyncMock(return_value=completed_action),
        ),
        patch(
            "app.ops_v9.service.OpsGovernanceBridge.remediation_policy",
            new=AsyncMock(return_value=_policy(executable=True)),
        ),
        patch(
            "app.ops_v9.service.OpsGovernanceBridge.event",
            new=AsyncMock(),
        ),
        patch(
            "app.ops_v9.service.OpsGovernanceBridge.resume_after_approval",
            new=AsyncMock(),
        ),
        patch(
            "app.ops_v9.service.OpsGovernanceBridge.finish",
            new=AsyncMock(),
        ),
        patch(
            "app.ops_v9.service.OpsAgentClient.restart",
            new=restart_mock,
        ),
        patch(
            "app.ops_v9.service.OpsAgentClient.wait_until_healthy",
            new=AsyncMock(
                return_value={
                    "container": incident.service,
                    "state": "running",
                    "health": "healthy",
                }
            ),
        ),
    ):
        payload = RemediationRequest(
            action="restart_container",
            reason="Stage 8 idempotent remediation validation.",
            approved=True,
            idempotency_key="stage8-same-key",
        )

        first = await OpsService.remediate_governed(
            incident.id,
            payload,
            session=SimpleNamespace(),
            user_id=uuid4(),
            run_id=uuid4(),
        )

        second = await OpsService.remediate_governed(
            incident.id,
            payload,
            session=SimpleNamespace(),
            user_id=uuid4(),
            run_id=uuid4(),
        )

    assert first.status == "completed"
    assert second.status == "completed"
    assert second.duplicate_detected is True

    assert create_action_mock.await_count == 2

    # Critical Stage 8 acceptance condition:
    # destructive side effect happened exactly once.
    assert restart_mock.await_count == 1


@pytest.mark.asyncio
async def test_stage9_blocked_run_survives_process_restart_and_can_resume():
    """
    Stage 9 contract test.

    Persistence itself is owned by PostgreSQL. Here we verify that a
    blocked governed remediation does not depend on process-local state:
    the subsequent approved call is reconstructed only from persisted
    identifiers and repository results.
    """

    incident_id = uuid4()
    run_id = uuid4()
    user_id = uuid4()

    persisted_incident = _incident(status="diagnosed")
    persisted_incident.id = incident_id

    blocked_action = _action(
        incident_id=incident_id,
        status="denied",
    )
    blocked_action.approved = False

    approved_action = _action(
        incident_id=incident_id,
        status="approved",
    )

    completed_action = _action(
        incident_id=incident_id,
        status="completed",
    )
    completed_action.id = approved_action.id

    events: list[str] = []

    async def capture_event(**kwargs):
        events.append(kwargs["event_type"])
        return SimpleNamespace()

    async def set_status(incident_id_arg, status):
        obj = _incident(status=status)
        obj.id = incident_id_arg
        return obj

    # Phase 1: process instance reaches blocked state.
    with (
        patch(
            "app.ops_v9.service.OpsRepository.get_incident",
            new=AsyncMock(return_value=persisted_incident),
        ),
        patch(
            "app.ops_v9.service.OpsRepository.create_action",
            new=AsyncMock(return_value=blocked_action),
        ),
        patch(
            "app.ops_v9.service.OpsRepository.finish_action",
            new=AsyncMock(return_value=blocked_action),
        ),
        patch(
            "app.ops_v9.service.OpsGovernanceBridge.remediation_policy",
            new=AsyncMock(return_value=_policy(executable=False)),
        ),
        patch(
            "app.ops_v9.service.OpsGovernanceBridge.event",
            new=AsyncMock(side_effect=capture_event),
        ),
    ):
        blocked = await OpsService.remediate_governed(
            incident_id,
            RemediationRequest(
                action="restart_container",
                reason="Stage 9 blocked before simulated restart.",
                approved=False,
                idempotency_key="stage9-block",
            ),
            session=SimpleNamespace(),
            user_id=user_id,
            run_id=run_id,
        )

    assert blocked.status == "denied"
    assert "ops.remediation_blocked" in events

    # Simulated process restart:
    # no object from phase 1 is required by the next service invocation.
    events.clear()

    restart_mock = AsyncMock(
        return_value={
            "status": "completed",
            "action": "restart_container",
            "container": persisted_incident.service,
            "state": "running",
        }
    )

    # Phase 2: a new invocation reconstructs state from repository data.
    with (
        patch(
            "app.ops_v9.service.OpsRepository.get_incident",
            new=AsyncMock(return_value=persisted_incident),
        ),
        patch(
            "app.ops_v9.service.OpsRepository.create_action",
            new=AsyncMock(return_value=approved_action),
        ),
        patch(
            "app.ops_v9.service.OpsRepository.set_incident_status",
            new=AsyncMock(side_effect=set_status),
        ),
        patch(
            "app.ops_v9.service.OpsRepository.finish_action",
            new=AsyncMock(return_value=completed_action),
        ),
        patch(
            "app.ops_v9.service.OpsGovernanceBridge.remediation_policy",
            new=AsyncMock(return_value=_policy(executable=True)),
        ),
        patch(
            "app.ops_v9.service.OpsGovernanceBridge.event",
            new=AsyncMock(side_effect=capture_event),
        ),
        patch(
            "app.ops_v9.service.OpsGovernanceBridge.resume_after_approval",
            new=AsyncMock(),
        ) as resume_mock,
        patch(
            "app.ops_v9.service.OpsGovernanceBridge.finish",
            new=AsyncMock(),
        ),
        patch(
            "app.ops_v9.service.OpsAgentClient.restart",
            new=restart_mock,
        ),
        patch(
            "app.ops_v9.service.OpsAgentClient.wait_until_healthy",
            new=AsyncMock(
                return_value={
                    "container": persisted_incident.service,
                    "state": "running",
                    "health": "healthy",
                }
            ),
        ),
    ):
        resumed = await OpsService.remediate_governed(
            incident_id,
            RemediationRequest(
                action="restart_container",
                reason="Stage 9 approval after simulated restart.",
                approved=True,
                idempotency_key="stage9-approved",
            ),
            session=SimpleNamespace(),
            user_id=user_id,
            run_id=run_id,
        )

    assert resumed.status == "completed"

    resume_mock.assert_awaited_once()
    assert (
        resume_mock.await_args.kwargs["run_id"]
        == run_id
    )
    assert (
        resume_mock.await_args.kwargs["user_id"]
        == user_id
    )

    restart_mock.assert_awaited_once()

    assert "human.approval_granted" in events
    assert "run.resumed" in events
    assert "ops.remediation_started" in events
    assert "ops.recovery_verified" in events