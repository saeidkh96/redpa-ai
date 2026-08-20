from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.governance_v10 import AgentRun, AgentRunEvent
from app.models.human_review import HumanReview


class GovernanceAnalyticsService:
    async def summary(
        self,
        *,
        session: AsyncSession,
        user_id: UUID,
    ) -> dict[str, Any]:
        run_result = await session.execute(
            select(AgentRun).where(
                AgentRun.user_id == user_id
            )
        )
        runs = list(run_result.scalars().all())

        review_result = await session.execute(
            select(HumanReview).where(
                HumanReview.user_id == user_id
            )
        )
        reviews = list(review_result.scalars().all())

        run_ids = [run.id for run in runs]

        events: list[AgentRunEvent] = []

        if run_ids:
            event_result = await session.execute(
                select(AgentRunEvent).where(
                    AgentRunEvent.run_id.in_(run_ids)
                )
            )
            events = list(event_result.scalars().all())

        approved = sum(
            review.status == "approved"
            for review in reviews
        )

        rejected = sum(
            review.status == "rejected"
            for review in reviews
        )

        pending = sum(
            review.status == "pending"
            for review in reviews
        )

        decided = approved + rejected

        blocked_runs = sum(
            run.status == "blocked"
            for run in runs
        )

        completed_runs = sum(
            run.status == "completed"
            for run in runs
        )

        failed_runs = sum(
            run.status == "failed"
            for run in runs
        )

        running_runs = sum(
            run.status == "running"
            for run in runs
        )

        approval_requested_events = sum(
            event.event_type == "approval.requested"
            for event in events
        )

        approval_approved_events = sum(
            event.event_type == "approval.approved"
            for event in events
        )

        approval_rejected_events = sum(
            event.event_type == "approval.rejected"
            for event in events
        )

        events_by_run: dict[UUID, list[AgentRunEvent]] = {}

        for event in events:
            events_by_run.setdefault(
                event.run_id,
                [],
            ).append(event)

        resumed_run_ids: set[UUID] = set()

        for run_id, run_events in events_by_run.items():
            ordered_events = sorted(
                run_events,
                key=lambda item: item.created_at,
            )

            approval_seen = False

            for event in ordered_events:
                if event.event_type == "approval.approved":
                    approval_seen = True
                    continue

                if (
                    approval_seen
                    and event.event_type == "run.running"
                ):
                    resumed_run_ids.add(run_id)
                    break

        resumed_runs = len(resumed_run_ids)

        decision_latencies: list[float] = []

        for review in reviews:
            if (
                review.reviewed_at is not None
                and review.created_at is not None
            ):
                latency = (
                    review.reviewed_at
                    - review.created_at
                ).total_seconds()

                if latency >= 0:
                    decision_latencies.append(latency)

        average_decision_latency_seconds = (
            round(
                sum(decision_latencies)
                / len(decision_latencies),
                3,
            )
            if decision_latencies
            else 0.0
        )

        approval_rate = (
            round(approved / decided * 100, 2)
            if decided
            else 0.0
        )

        rejection_rate = (
            round(rejected / decided * 100, 2)
            if decided
            else 0.0
        )

        return {
            "version": "19.1.0",
            "source": "persisted-governance-state",
            "agent_runs": {
                "total": len(runs),
                "running": running_runs,
                "blocked": blocked_runs,
                "completed": completed_runs,
                "failed": failed_runs,
                "resumed": resumed_runs,
            },
            "approvals": {
                "total": len(reviews),
                "pending": pending,
                "approved": approved,
                "rejected": rejected,
                "approval_rate_percent": approval_rate,
                "rejection_rate_percent": rejection_rate,
                "average_decision_latency_seconds": (
                    average_decision_latency_seconds
                ),
            },
            "governance_events": {
                "total": len(events),
                "approval_requested": (
                    approval_requested_events
                ),
                "approval_approved": (
                    approval_approved_events
                ),
                "approval_rejected": (
                    approval_rejected_events
                ),
            },
        }

    async def evidence(
        self,
        *,
        session: AsyncSession,
        user_id: UUID,
    ) -> dict[str, Any]:
        run_result = await session.execute(
            select(AgentRun)
            .where(AgentRun.user_id == user_id)
            .order_by(AgentRun.created_at.desc())
            .limit(100)
        )
        runs = list(run_result.scalars().all())

        review_result = await session.execute(
            select(HumanReview)
            .where(HumanReview.user_id == user_id)
            .order_by(HumanReview.created_at.desc())
            .limit(100)
        )
        reviews = list(review_result.scalars().all())

        run_ids = [run.id for run in runs]

        events: list[AgentRunEvent] = []

        if run_ids:
            event_result = await session.execute(
                select(AgentRunEvent)
                .where(
                    AgentRunEvent.run_id.in_(run_ids)
                )
                .order_by(
                    AgentRunEvent.created_at.desc()
                )
                .limit(500)
            )
            events = list(event_result.scalars().all())

        return {
            "version": "19.1.0",
            "generated_from": [
                "agent_runs",
                "agent_run_events",
                "human_reviews",
            ],
            "runs": [
                {
                    "id": str(run.id),
                    "agent_id": run.agent_id,
                    "workflow_id": run.workflow_id,
                    "trace_id": run.trace_id,
                    "status": run.status,
                    "objective": run.objective,
                    "evaluation_score": (
                        run.evaluation_score
                    ),
                    "created_at": (
                        run.created_at.isoformat()
                    ),
                    "updated_at": (
                        run.updated_at.isoformat()
                    ),
                }
                for run in runs
            ],
            "approvals": [
                {
                    "id": str(review.id),
                    "conversation_id": str(
                        review.conversation_id
                    ),
                    "status": review.status,
                    "requested_action": (
                        review.requested_action
                    ),
                    "reviewer_feedback": (
                        review.reviewer_feedback
                    ),
                    "reviewed_by": (
                        str(review.reviewed_by)
                        if review.reviewed_by
                        else None
                    ),
                    "created_at": (
                        review.created_at.isoformat()
                    ),
                    "reviewed_at": (
                        review.reviewed_at.isoformat()
                        if review.reviewed_at
                        else None
                    ),
                    "action_payload": (
                        review.action_payload
                    ),
                }
                for review in reviews
            ],
            "events": [
                {
                    "id": str(event.id),
                    "run_id": str(event.run_id),
                    "event_type": event.event_type,
                    "stage": event.stage,
                    "trace_id": event.trace_id,
                    "payload": event.payload,
                    "created_at": (
                        event.created_at.isoformat()
                    ),
                }
                for event in events
            ],
        }


governance_analytics_service = (
    GovernanceAnalyticsService()
)
