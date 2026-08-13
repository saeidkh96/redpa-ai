from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.conversation import Conversation
from app.models.human_review import (
    HumanReview,
    HumanReviewStatus,
)
from app.models.message import (
    Message,
    MessageRole,
    MessageStatus,
)
from app.schemas.orchestrator import OrchestratorResult
from app.services.message_service import MessageService
from app.services.orchestrator_service import (
    OrchestratorService,
)


class WorkflowResumeError(Exception):
    """
    Base exception for human-review workflow resume errors.
    """


class WorkflowResumeReviewNotFoundError(
    WorkflowResumeError
):
    """
    Raised when the requested human review does not exist or does
    not belong to the requesting user.
    """


class WorkflowResumeNotApprovedError(
    WorkflowResumeError
):
    """
    Raised when attempting to resume a review that has not been
    approved.
    """


class WorkflowAlreadyResumedError(
    WorkflowResumeError
):
    """
    Raised when an approved review has already been resumed.
    """


class WorkflowResumeConversationNotFoundError(
    WorkflowResumeError
):
    """
    Raised when the conversation associated with a human review
    cannot be found.
    """


@dataclass(slots=True)
class WorkflowResumeResult:
    review: HumanReview
    conversation: Conversation
    assistant_message: Message
    orchestrator_result: OrchestratorResult


class WorkflowResumeService:
    @classmethod
    async def resume_approved_review(
        cls,
        *,
        session: AsyncSession,
        review_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkflowResumeResult:
        review = await cls._get_review_for_resume(
            session=session,
            review_id=review_id,
            user_id=user_id,
        )

        cls._validate_review_can_resume(
            review,
        )

        conversation = await cls._get_conversation(
            session=session,
            conversation_id=review.conversation_id,
            user_id=user_id,
        )

        history = await MessageService.get_recent_for_llm(
            session=session,
            conversation_id=conversation.id,
            limit=settings.ollama_max_context_messages,
        )

        action_payload = cls._build_resume_action_payload(
            review,
        )

        try:
            orchestrator_result = (
                await OrchestratorService.resume(
                    conversation_id=conversation.id,
                    user_id=user_id,
                    history=history,
                    review_id=review.id,
                    requested_action=review.requested_action,
                    request_content=review.request_content,
                    action_payload=action_payload,
                    reviewed_by=review.reviewed_by,
                    reviewed_at=review.reviewed_at,
                    reviewer_feedback=review.reviewer_feedback,
                )
            )

            assistant_message = (
                await MessageService.create_internal_message(
                    session=session,
                    conversation=conversation,
                    role=MessageRole.ASSISTANT,
                    content=(
                        orchestrator_result.response_content
                    ),
                    status=MessageStatus.COMPLETED,
                    agent_name="workflow_resume",
                    extra_data=(
                        cls._build_message_metadata(
                            review=review,
                            orchestrator_result=(
                                orchestrator_result
                            ),
                        )
                    ),
                    commit=False,
                )
            )

            cls._mark_review_as_resumed(
                review=review,
                assistant_message=assistant_message,
                orchestrator_result=orchestrator_result,
            )

            await session.commit()

            await session.refresh(
                review,
            )

            await session.refresh(
                assistant_message,
            )

            return WorkflowResumeResult(
                review=review,
                conversation=conversation,
                assistant_message=assistant_message,
                orchestrator_result=orchestrator_result,
            )

        except Exception:
            await session.rollback()
            raise

    @staticmethod
    async def _get_review_for_resume(
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

        result = await session.execute(
            statement,
        )

        review = result.scalar_one_or_none()

        if review is None:
            raise WorkflowResumeReviewNotFoundError(
                "Human review not found.",
            )

        return review

    @staticmethod
    def _validate_review_can_resume(
        review: HumanReview,
    ) -> None:
        if review.status != HumanReviewStatus.APPROVED.value:
            raise WorkflowResumeNotApprovedError(
                (
                    "Only an approved human review can be "
                    "resumed."
                ),
            )

        action_payload = review.action_payload

        if not isinstance(
            action_payload,
            dict,
        ):
            return

        resume_completed = bool(
            action_payload.get(
                "resume_completed",
                False,
            )
        )

        resumed_assistant_message_id = (
            WorkflowResumeService._optional_string(
                action_payload.get(
                    "resumed_assistant_message_id",
                )
            )
        )

        if (
            resume_completed
            or resumed_assistant_message_id is not None
        ):
            raise WorkflowAlreadyResumedError(
                (
                    "This approved human review has already "
                    "been resumed."
                ),
            )

    @staticmethod
    async def _get_conversation(
        *,
        session: AsyncSession,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Conversation:
        statement = select(
            Conversation,
        ).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )

        result = await session.execute(
            statement,
        )

        conversation = result.scalar_one_or_none()

        if conversation is None:
            raise WorkflowResumeConversationNotFoundError(
                (
                    "The conversation associated with this "
                    "human review was not found."
                ),
            )

        return conversation

    @staticmethod
    def _build_resume_action_payload(
        review: HumanReview,
    ) -> dict[str, Any]:
        existing_payload = (
            review.action_payload
            if isinstance(
                review.action_payload,
                dict,
            )
            else {}
        )

        resume_route = (
            WorkflowResumeService._optional_string(
                existing_payload.get(
                    "resume_route",
                )
            )
            or WorkflowResumeService._optional_string(
                existing_payload.get(
                    "original_route",
                )
            )
            or WorkflowResumeService._infer_resume_route(
                requested_action=review.requested_action,
                request_content=review.request_content,
            )
        )

        return {
            **existing_payload,
            "original_route": (
                WorkflowResumeService._optional_string(
                    existing_payload.get(
                        "original_route",
                    )
                )
                or resume_route
            ),
            "resume_route": resume_route,
            "requested_action": review.requested_action,
            "request_content": review.request_content,
            "approval_required": False,
            "approval_granted": True,
            "approved_review_id": str(
                review.id,
            ),
            "resume_started_at": datetime.now(
                timezone.utc,
            ).isoformat(),
            "resume_completed": False,
        }

    @staticmethod
    def _infer_resume_route(
        *,
        requested_action: str | None,
        request_content: str | None,
    ) -> str:
        combined_text = " ".join(
            value
            for value in (
                requested_action,
                request_content,
            )
            if isinstance(
                value,
                str,
            )
        ).casefold()

        sql_signals = (
            "sql",
            "database",
            "postgres",
            "postgresql",
            "mysql",
            "select from",
            "insert into",
            "update table",
            "delete from",
            "drop table",
            "truncate",
        )

        if any(
            signal in combined_text
            for signal in sql_signals
        ):
            return "sql"

        tool_signals = (
            "send email",
            "send an email",
            "email someone",
            "calendar",
            "schedule a meeting",
            "github issue",
            "call api",
            "execute tool",
            "transfer money",
            "wire money",
            "payment",
            "purchase",
            "buy",
            "refund",
            "approve invoice",
        )

        if any(
            signal in combined_text
            for signal in tool_signals
        ):
            return "tool"

        rag_signals = (
            "document",
            "documents",
            "pdf",
            "file",
            "knowledge base",
            "retrieval",
            "embedding",
            "vector store",
        )

        if any(
            signal in combined_text
            for signal in rag_signals
        ):
            return "rag"

        research_signals = (
            "research",
            "web search",
            "search online",
            "browse the web",
            "latest news",
            "external sources",
        )

        if any(
            signal in combined_text
            for signal in research_signals
        ):
            return "research"

        return "chat"

    @staticmethod
    def _mark_review_as_resumed(
        *,
        review: HumanReview,
        assistant_message: Message,
        orchestrator_result: OrchestratorResult,
    ) -> None:
        existing_payload = (
            review.action_payload
            if isinstance(
                review.action_payload,
                dict,
            )
            else {}
        )

        review.action_payload = {
            **existing_payload,
            "approval_required": False,
            "approval_granted": True,
            "approved_review_id": str(
                review.id,
            ),
            "resume_completed": True,
            "resume_completed_at": datetime.now(
                timezone.utc,
            ).isoformat(),
            "resumed_assistant_message_id": str(
                assistant_message.id,
            ),
            "resumed_route": orchestrator_result.route,
            "resumed_model": orchestrator_result.model,
            "resumed_provider": (
                orchestrator_result.provider
            ),
        }

    @staticmethod
    def _build_message_metadata(
        *,
        review: HumanReview,
        orchestrator_result: OrchestratorResult,
    ) -> dict[str, Any]:
        return {
            "provider": orchestrator_result.provider,
            "model": orchestrator_result.model,
            "workflow": "langgraph_resume",
            "route": orchestrator_result.route,
            "planner_reason": (
                orchestrator_result.planner_reason
            ),
            "usage": orchestrator_result.usage,
            "streamed": False,
            "resumed": True,
            "approval_granted": True,
            "approved_review_id": str(
                review.id,
            ),
            "review_status": review.status,
            "requested_action": review.requested_action,
            "reviewer_feedback": (
                review.reviewer_feedback
            ),
            "requires_human_review": (
                orchestrator_result.requires_human_review
            ),
        }

    @staticmethod
    def _optional_string(
        value: Any,
    ) -> str | None:
        if value is None:
            return None

        normalized_value = str(
            value,
        ).strip()

        if not normalized_value:
            return None

        return normalized_value