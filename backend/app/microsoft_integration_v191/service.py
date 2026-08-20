from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.governance_v10.repository import AgentRunNotFoundError
from app.governance_v10.schemas import AgentRunEventCreate
from app.governance_v10.service import (
    AgentGovernanceService,
    InvalidAgentRunTransitionError,
)
from app.models.human_review import HumanReviewStatus
from app.services.human_review_service import (
    HumanReviewAlreadyDecidedError,
    HumanReviewNotFoundError,
    HumanReviewService,
)

from .schemas import (
    MicrosoftApprovalDecision,
    MicrosoftApprovalDecisionResult,
    MicrosoftApprovalEnvelope,
    MicrosoftApprovalRequest,
)


class MicrosoftGovernedApprovalService:
    def __init__(self) -> None:
        self._governance = AgentGovernanceService()

    async def create_approval(
        self,
        *,
        session: AsyncSession,
        user_id: UUID,
        payload: MicrosoftApprovalRequest,
    ) -> MicrosoftApprovalEnvelope:
        action_payload = {
            "integration": "microsoft",
            "connector": "power-automate",
            "incident_id": (
                str(payload.incident_id)
                if payload.incident_id
                else None
            ),
            "agent_run_id": (
                str(payload.agent_run_id)
                if payload.agent_run_id
                else None
            ),
            "severity": payload.severity,
            "title": payload.title,
            "callback_url": (
                str(payload.callback_url)
                if payload.callback_url
                else None
            ),
            "approval_required": True,
            "approval_granted": False,
            "metadata": payload.metadata,
        }

        review = await HumanReviewService.create(
            session=session,
            user_id=user_id,
            conversation_id=payload.conversation_id,
            message_id=payload.message_id,
            reason=(
                "Microsoft Power Automate approval requested: "
                f"{payload.summary}"
            ),
            requested_action=payload.requested_action,
            request_content=payload.request_content,
            action_payload=action_payload,
        )

        if payload.agent_run_id is not None:
            try:
                await self._governance.add_event(
                    session=session,
                    run_id=payload.agent_run_id,
                    user_id=user_id,
                    payload=AgentRunEventCreate(
                        event_type="approval.requested",
                        stage="microsoft_integration",
                        payload={
                            "review_id": str(review.id),
                            "incident_id": (
                                str(payload.incident_id)
                                if payload.incident_id
                                else None
                            ),
                            "connector": "power-automate",
                            "severity": payload.severity,
                        },
                    ),
                )
            except AgentRunNotFoundError:
                pass

        return MicrosoftApprovalEnvelope(
            review_id=review.id,
            conversation_id=review.conversation_id,
            incident_id=payload.incident_id,
            agent_run_id=payload.agent_run_id,
            title=payload.title,
            summary=payload.summary,
            severity=payload.severity,
            requested_action=payload.requested_action,
            callback_url=payload.callback_url,
            metadata={
                **payload.metadata,
                "created_at": datetime.now(
                    timezone.utc
                ).isoformat(),
                "boundary": "human-approval",
            },
        )

    async def apply_decision(
        self,
        *,
        session: AsyncSession,
        user_id: UUID,
        review_id: UUID,
        payload: MicrosoftApprovalDecision,
    ) -> MicrosoftApprovalDecisionResult:
        review = await HumanReviewService.get_by_id(
            session=session,
            review_id=review_id,
            user_id=user_id,
        )

        if review is None:
            raise HumanReviewNotFoundError(
                "Human review not found."
            )

        if payload.decision == "approved":
            review = await HumanReviewService.approve(
                session=session,
                review_id=review_id,
                user_id=user_id,
                reviewer_id=user_id,
                feedback=payload.feedback,
            )
        else:
            review = await HumanReviewService.reject(
                session=session,
                review_id=review_id,
                user_id=user_id,
                reviewer_id=user_id,
                feedback=payload.feedback,
            )

        existing_action_payload = (
            review.action_payload
            if isinstance(review.action_payload, dict)
            else {}
        )

        if payload.decision == "approved":
            review.action_payload = {
                **existing_action_payload,
                "approval_required": False,
                "approval_granted": True,
                "approved_review_id": str(review.id),
                "approval_decision": "approved",
                "approval_decided_at": datetime.now(
                    timezone.utc
                ).isoformat(),
                "approval_feedback": payload.feedback,
                "approval_metadata": payload.metadata,
            }
        else:
            review.action_payload = {
                **existing_action_payload,
                "approval_required": False,
                "approval_granted": False,
                "approval_decision": "rejected",
                "approval_decided_at": datetime.now(
                    timezone.utc
                ).isoformat(),
                "approval_feedback": payload.feedback,
                "approval_metadata": payload.metadata,
            }

        await session.commit()
        await session.refresh(review)

        agent_run_id = payload.agent_run_id

        if agent_run_id is None:
            raw_agent_run_id = (
                review.action_payload or {}
            ).get("agent_run_id")

            if raw_agent_run_id:
                try:
                    agent_run_id = UUID(
                        str(raw_agent_run_id)
                    )
                except ValueError:
                    agent_run_id = None

        run_status = None
        audit_recorded = False

        if agent_run_id is not None:
            try:
                await self._governance.add_event(
                    session=session,
                    run_id=agent_run_id,
                    user_id=user_id,
                    payload=AgentRunEventCreate(
                        event_type=(
                            f"approval.{payload.decision}"
                        ),
                        stage="microsoft_integration",
                        payload={
                            "review_id": str(review.id),
                            "incident_id": (
                                str(payload.incident_id)
                                if payload.incident_id
                                else None
                            ),
                            "connector": "power-automate",
                            "feedback": payload.feedback,
                            "metadata": payload.metadata,
                        },
                    ),
                )

                audit_recorded = True

                if payload.decision == "approved":
                    try:
                        run = await self._governance.resume_run(
                            session=session,
                            run_id=agent_run_id,
                            user_id=user_id,
                        )
                        run_status = run.status
                    except InvalidAgentRunTransitionError:
                        run_status = None

            except AgentRunNotFoundError:
                agent_run_id = None

        approved = (
            review.status
            == HumanReviewStatus.APPROVED.value
        )

        return MicrosoftApprovalDecisionResult(
            review_id=review.id,
            decision=payload.decision,
            review_status=review.status,
            agent_run_id=agent_run_id,
            agent_run_status=run_status,
            resume_allowed=approved,
            audit_event_recorded=audit_recorded,
        )


microsoft_governed_approval_service = (
    MicrosoftGovernedApprovalService()
)
