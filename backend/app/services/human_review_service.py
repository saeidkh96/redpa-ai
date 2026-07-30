from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.human_review import (
    HumanReview,
    HumanReviewStatus,
)


class HumanReviewNotFoundError(Exception):
    """
    Raised when a human review cannot be found or does not belong
    to the requesting user.
    """


class HumanReviewAlreadyDecidedError(Exception):
    """
    Raised when attempting to approve or reject a review that is
    no longer pending.
    """


class HumanReviewService:
    @staticmethod
    async def create(
        *,
        session: AsyncSession,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        reason: str,
        message_id: uuid.UUID | None = None,
        requested_action: str | None = None,
        request_content: str | None = None,
        action_payload: dict[str, Any] | None = None,
        commit: bool = True,
    ) -> HumanReview:
        review = HumanReview(
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            status=HumanReviewStatus.PENDING.value,
            reason=reason,
            requested_action=requested_action,
            request_content=request_content,
            action_payload=action_payload,
        )

        session.add(review)

        if commit:
            await session.commit()
            await session.refresh(review)
        else:
            await session.flush()

        return review

    @staticmethod
    async def get_by_id(
        *,
        session: AsyncSession,
        review_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> HumanReview | None:
        statement = select(HumanReview).where(
            HumanReview.id == review_id,
            HumanReview.user_id == user_id,
        )

        result = await session.execute(statement)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_for_user(
        *,
        session: AsyncSession,
        user_id: uuid.UUID,
        limit: int,
        offset: int,
        review_status: HumanReviewStatus | None = None,
    ) -> tuple[list[HumanReview], int]:
        filters = [
            HumanReview.user_id == user_id,
        ]

        if review_status is not None:
            filters.append(
                HumanReview.status == review_status.value,
            )

        statement = (
            select(HumanReview)
            .where(*filters)
            .order_by(
                HumanReview.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        count_statement = (
            select(func.count())
            .select_from(HumanReview)
            .where(*filters)
        )

        result = await session.execute(statement)
        count_result = await session.execute(count_statement)

        reviews = list(result.scalars().all())
        total = count_result.scalar_one()

        return reviews, total

    @staticmethod
    async def approve(
        *,
        session: AsyncSession,
        review_id: uuid.UUID,
        user_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        feedback: str | None = None,
    ) -> HumanReview:
        review = await HumanReviewService._get_pending_review_for_update(
            session=session,
            review_id=review_id,
            user_id=user_id,
        )

        review.approve(
            reviewer_id=reviewer_id,
            feedback=HumanReviewService._normalize_feedback(
                feedback,
            ),
        )

        await session.commit()
        await session.refresh(review)

        return review

    @staticmethod
    async def reject(
        *,
        session: AsyncSession,
        review_id: uuid.UUID,
        user_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        feedback: str | None = None,
    ) -> HumanReview:
        review = await HumanReviewService._get_pending_review_for_update(
            session=session,
            review_id=review_id,
            user_id=user_id,
        )

        review.reject(
            reviewer_id=reviewer_id,
            feedback=HumanReviewService._normalize_feedback(
                feedback,
            ),
        )

        await session.commit()
        await session.refresh(review)

        return review

    @staticmethod
    async def _get_pending_review_for_update(
        *,
        session: AsyncSession,
        review_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> HumanReview:
        statement = (
            select(HumanReview)
            .where(
                HumanReview.id == review_id,
                HumanReview.user_id == user_id,
            )
            .with_for_update()
        )

        result = await session.execute(statement)
        review = result.scalar_one_or_none()

        if review is None:
            raise HumanReviewNotFoundError(
                "Human review not found.",
            )

        if review.status != HumanReviewStatus.PENDING.value:
            raise HumanReviewAlreadyDecidedError(
                (
                    "This human review has already been "
                    f"{review.status}."
                ),
            )

        return review

    @staticmethod
    def _normalize_feedback(
        feedback: str | None,
    ) -> str | None:
        if feedback is None:
            return None

        normalized_feedback = feedback.strip()

        if not normalized_feedback:
            return None

        return normalized_feedback