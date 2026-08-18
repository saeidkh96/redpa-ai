from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.adaptive_governance_v13.engine import adaptive_policy_engine
from app.adaptive_governance_v13.policy_adapter import policy_application_adapter
from app.adaptive_governance_v13.repository import AdaptiveGovernanceRepository
from app.adaptive_governance_v13.schemas import (
    GovernanceSignalCreate,
    GovernanceSummaryResponse,
    PolicyProposalCreate,
    PolicyRecommendationRequest,
    ProposalApplyRequest,
    ProposalReviewRequest,
    ProposalRollbackRequest,
    ShadowEvaluationRequest,
    ShadowEvaluationResponse,
)


class ProposalNotFoundError(LookupError):
    pass


class InvalidProposalTransitionError(RuntimeError):
    pass


class AdaptiveGovernanceService:
    async def ingest_signal(
        self,
        *,
        session: AsyncSession,
        user_id: UUID,
        payload: GovernanceSignalCreate,
    ):
        return await AdaptiveGovernanceRepository.add_signal(
            session=session, user_id=user_id, payload=payload
        )

    async def recommend(
        self,
        *,
        session: AsyncSession,
        user_id: UUID,
        payload: PolicyRecommendationRequest,
    ):
        signals = await AdaptiveGovernanceRepository.recent_signals(
            session=session,
            user_id=user_id,
            action=payload.action,
            limit=payload.window_size,
            agent_id=payload.agent_id,
            tenant_id=payload.tenant_id,
        )
        return adaptive_policy_engine.recommend(action=payload.action, signals=signals)

    async def create_proposal(
        self,
        *,
        session: AsyncSession,
        user_id: UUID,
        payload: PolicyProposalCreate,
    ):
        return await AdaptiveGovernanceRepository.create_proposal(
            session=session, user_id=user_id, payload=payload
        )

    async def review(
        self,
        *,
        session: AsyncSession,
        user_id: UUID,
        reviewer_id: UUID,
        proposal_id: UUID,
        payload: ProposalReviewRequest,
    ):
        row = await self._proposal(session=session, user_id=user_id, proposal_id=proposal_id)
        if row.status not in {"proposed", "review_required"}:
            raise InvalidProposalTransitionError(
                f"Proposal in status '{row.status}' cannot be reviewed."
            )
        row.status = "approved" if payload.approved else "rejected"
        row.approved_by = reviewer_id if payload.approved else None
        row.source_evidence = {
            **(row.source_evidence or {}),
            "review_reason": payload.reason,
        }
        return await AdaptiveGovernanceRepository.save(session=session, row=row)

    async def shadow_evaluate(
        self,
        *,
        session: AsyncSession,
        user_id: UUID,
        proposal_id: UUID,
        payload: ShadowEvaluationRequest,
    ) -> ShadowEvaluationResponse:
        row = await self._proposal(session=session, user_id=user_id, proposal_id=proposal_id)

        observed = max(payload.observed_actions, 1)
        good = payload.blocked_bad_actions
        harm = payload.blocked_good_actions + payload.escaped_bad_actions
        score = max(0.0, min(1.0, 0.5 + (good - harm) / observed))

        reasons = []
        if payload.blocked_good_actions:
            reasons.append("Candidate policy would block known-good actions.")
        if payload.escaped_bad_actions:
            reasons.append("Candidate policy would allow known-bad actions.")
        if payload.blocked_bad_actions:
            reasons.append("Candidate policy blocks known-bad actions.")

        safe = score >= 0.70 and payload.blocked_good_actions == 0 and payload.escaped_bad_actions == 0
        row.source_evidence = {
            **(row.source_evidence or {}),
            "shadow_evaluation": {
                **payload.model_dump(),
                "score": round(score, 4),
                "safe_to_apply": safe,
            },
        }
        await AdaptiveGovernanceRepository.save(session=session, row=row)

        return ShadowEvaluationResponse(
            proposal_id=row.id,
            safe_to_apply=safe,
            score=round(score, 4),
            reasons=reasons or ["No adverse shadow-evaluation evidence observed."],
        )

    async def apply(
        self,
        *,
        session: AsyncSession,
        user_id: UUID,
        proposal_id: UUID,
        payload: ProposalApplyRequest,
    ):
        row = await self._proposal(session=session, user_id=user_id, proposal_id=proposal_id)
        if row.status != "approved":
            raise InvalidProposalTransitionError("Only explicitly approved proposals can be applied.")

        shadow = (row.source_evidence or {}).get("shadow_evaluation") or {}
        if not shadow.get("safe_to_apply"):
            raise InvalidProposalTransitionError(
                "Proposal must pass shadow evaluation before application."
            )

        row.previous_state = row.applied_state or {}
        row.applied_state = await policy_application_adapter.apply(row)
        row.status = "applied"
        row.auto_applied = False
        row.applied_at = datetime.now(timezone.utc)
        return await AdaptiveGovernanceRepository.save(session=session, row=row)

    async def rollback(
        self,
        *,
        session: AsyncSession,
        user_id: UUID,
        proposal_id: UUID,
        payload: ProposalRollbackRequest,
    ):
        row = await self._proposal(session=session, user_id=user_id, proposal_id=proposal_id)
        if row.status != "applied":
            raise InvalidProposalTransitionError("Only applied proposals can be rolled back.")

        rollback_result = await policy_application_adapter.rollback(
            proposal=row,
            previous_state=row.previous_state or {},
        )
        row.status = "rolled_back"
        row.rolled_back_at = datetime.now(timezone.utc)
        row.source_evidence = {
            **(row.source_evidence or {}),
            "rollback_reason": payload.reason,
            "rollback_result": rollback_result,
        }
        return await AdaptiveGovernanceRepository.save(session=session, row=row)

    async def summary(
        self,
        *,
        session: AsyncSession,
        user_id: UUID,
    ) -> GovernanceSummaryResponse:
        proposals = await AdaptiveGovernanceRepository.list_proposals(
            session=session, user_id=user_id
        )
        return GovernanceSummaryResponse(
            total_signals=0,
            total_proposals=len(proposals),
            review_required=sum(p.status == "review_required" for p in proposals),
            approved=sum(p.status == "approved" for p in proposals),
            applied=sum(p.status == "applied" for p in proposals),
            rolled_back=sum(p.status == "rolled_back" for p in proposals),
        )

    @staticmethod
    async def _proposal(
        *,
        session: AsyncSession,
        user_id: UUID,
        proposal_id: UUID,
    ):
        row = await AdaptiveGovernanceRepository.get_proposal(
            session=session, user_id=user_id, proposal_id=proposal_id
        )
        if row is None:
            raise ProposalNotFoundError(f"Adaptive policy proposal '{proposal_id}' was not found.")
        return row


adaptive_governance_service = AdaptiveGovernanceService()
