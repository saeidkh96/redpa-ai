from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    LLMInvalidResponseError,
    LLMServiceError,
)
from app.models.conversation import Conversation
from app.models.human_review import HumanReview
from app.models.message import (
    Message,
    MessageRole,
    MessageStatus,
)
from app.schemas.orchestrator import OrchestratorResult
from app.services.human_review_service import (
    HumanReviewService,
)
from app.services.message_service import MessageService
from app.services.orchestrator_service import (
    OrchestratorService,
)


class ChatService:
    @staticmethod
    async def generate_response(
        session: AsyncSession,
        conversation: Conversation,
        content: str,
    ) -> tuple[Message, Message, str]:
        cleaned_content = content.strip()

        if not cleaned_content:
            raise ValueError(
                "Chat message content cannot be empty."
            )

        user_message = (
            await MessageService.create_user_message(
                session=session,
                conversation=conversation,
                content=cleaned_content,
                commit=False,
            )
        )

        await session.commit()
        await session.refresh(user_message)

        history = await MessageService.get_recent_for_llm(
            session=session,
            conversation_id=conversation.id,
            limit=settings.ollama_max_context_messages,
        )

        try:
            orchestrator_result = (
                await OrchestratorService.run(
                    conversation_id=conversation.id,
                    user_id=conversation.user_id,
                    history=history,
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
                    agent_name="orchestrator",
                    extra_data=(
                        ChatService._build_message_metadata(
                            orchestrator_result=(
                                orchestrator_result
                            ),
                            streamed=False,
                        )
                    ),
                    commit=True,
                )
            )

            human_review = (
                await ChatService._create_human_review_if_required(
                    session=session,
                    conversation=conversation,
                    user_message=user_message,
                    assistant_message=assistant_message,
                    orchestrator_result=orchestrator_result,
                    fallback_request_content=cleaned_content,
                )
            )

            if human_review is not None:
                await ChatService._attach_review_to_message(
                    session=session,
                    assistant_message=assistant_message,
                    human_review=human_review,
                )

            return (
                user_message,
                assistant_message,
                orchestrator_result.model,
            )

        except LLMServiceError:
            await ChatService._store_failed_response(
                session=session,
                conversation=conversation,
            )

            raise

        except Exception:
            await session.rollback()
            raise

    @staticmethod
    async def stream_response(
        session: AsyncSession,
        conversation: Conversation,
        content: str,
    ) -> AsyncIterator[dict[str, Any]]:
        cleaned_content = content.strip()

        if not cleaned_content:
            raise ValueError(
                "Chat message content cannot be empty."
            )

        user_message = (
            await MessageService.create_user_message(
                session=session,
                conversation=conversation,
                content=cleaned_content,
                commit=False,
            )
        )

        await session.commit()
        await session.refresh(user_message)

        yield {
            "event": "user_message_created",
            "data": {
                "conversation_id": str(
                    conversation.id
                ),
                "message_id": str(
                    user_message.id
                ),
                "role": MessageRole.USER.value,
                "content": user_message.content,
                "status": user_message.status,
            },
        }

        history = await MessageService.get_recent_for_llm(
            session=session,
            conversation_id=conversation.id,
            limit=settings.ollama_max_context_messages,
        )

        workflow_completed_data: dict[str, Any] | None = None

        try:
            async for stream_event in (
                OrchestratorService.stream(
                    conversation_id=conversation.id,
                    user_id=conversation.user_id,
                    history=history,
                )
            ):
                event_name = str(
                    stream_event.get(
                        "event",
                        "message",
                    )
                )

                event_data = stream_event.get(
                    "data",
                    {},
                )

                if not isinstance(event_data, dict):
                    event_data = {
                        "value": event_data,
                    }

                if event_name == "workflow_completed":
                    workflow_completed_data = event_data
                    continue

                yield {
                    "event": event_name,
                    "data": event_data,
                }

            if workflow_completed_data is None:
                raise LLMInvalidResponseError(
                    "The streamed agent workflow did not "
                    "return a completion event."
                )

            orchestrator_result = (
                ChatService._build_streamed_result(
                    workflow_completed_data
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
                    agent_name="orchestrator",
                    extra_data=(
                        ChatService._build_message_metadata(
                            orchestrator_result=(
                                orchestrator_result
                            ),
                            streamed=True,
                        )
                    ),
                    commit=True,
                )
            )

            human_review = (
                await ChatService._create_human_review_if_required(
                    session=session,
                    conversation=conversation,
                    user_message=user_message,
                    assistant_message=assistant_message,
                    orchestrator_result=orchestrator_result,
                    fallback_request_content=cleaned_content,
                )
            )

            if human_review is not None:
                await ChatService._attach_review_to_message(
                    session=session,
                    assistant_message=assistant_message,
                    human_review=human_review,
                )

                yield {
                    "event": "human_review_created",
                    "data": {
                        "review_id": str(
                            human_review.id
                        ),
                        "conversation_id": str(
                            human_review.conversation_id
                        ),
                        "message_id": (
                            str(human_review.message_id)
                            if human_review.message_id
                            else None
                        ),
                        "status": human_review.status,
                        "reason": human_review.reason,
                        "requested_action": (
                            human_review.requested_action
                        ),
                    },
                }

            yield {
                "event": "workflow_completed",
                "data": {
                    "conversation_id": str(
                        conversation.id
                    ),
                    "user_message_id": str(
                        user_message.id
                    ),
                    "assistant_message_id": str(
                        assistant_message.id
                    ),
                    "response_content": (
                        orchestrator_result.response_content
                    ),
                    "model": orchestrator_result.model,
                    "provider": orchestrator_result.provider,
                    "route": orchestrator_result.route,
                    "planner_reason": (
                        orchestrator_result.planner_reason
                    ),
                    "usage": orchestrator_result.usage,
                    "requires_human_review": (
                        orchestrator_result
                        .requires_human_review
                    ),
                    "review_id": (
                        str(human_review.id)
                        if human_review is not None
                        else None
                    ),
                    "review_status": (
                        human_review.status
                        if human_review is not None
                        else orchestrator_result.review_status
                    ),
                    "review_reason": (
                        human_review.reason
                        if human_review is not None
                        else orchestrator_result.review_reason
                    ),
                    "requested_action": (
                        human_review.requested_action
                        if human_review is not None
                        else orchestrator_result
                        .requested_action
                    ),
                },
            }

        except LLMServiceError:
            await ChatService._store_failed_response(
                session=session,
                conversation=conversation,
            )

            raise

        except Exception:
            await ChatService._store_failed_response(
                session=session,
                conversation=conversation,
            )

            raise

    @staticmethod
    async def _create_human_review_if_required(
        *,
        session: AsyncSession,
        conversation: Conversation,
        user_message: Message,
        assistant_message: Message,
        orchestrator_result: OrchestratorResult,
        fallback_request_content: str,
    ) -> HumanReview | None:
        if not orchestrator_result.requires_human_review:
            return None

        review_reason = (
            orchestrator_result.review_reason
            or orchestrator_result.planner_reason
            or "The request requires human review."
        )

        request_content = (
            orchestrator_result.request_content
            or fallback_request_content
        )

        requested_action = (
            orchestrator_result.requested_action
            or orchestrator_result.route
            or "workflow_execution"
        )

        action_payload = (
            orchestrator_result.action_payload
        )

        if action_payload is None:
            action_payload = {
                "route": orchestrator_result.route,
                "planner_reason": (
                    orchestrator_result.planner_reason
                ),
                "user_message_id": str(
                    user_message.id
                ),
                "assistant_message_id": str(
                    assistant_message.id
                ),
            }

        human_review = await HumanReviewService.create(
            session=session,
            user_id=conversation.user_id,
            conversation_id=conversation.id,
            message_id=user_message.id,
            reason=review_reason,
            requested_action=requested_action,
            request_content=request_content,
            action_payload=action_payload,
            commit=True,
        )

        return human_review

    @staticmethod
    async def _attach_review_to_message(
        *,
        session: AsyncSession,
        assistant_message: Message,
        human_review: HumanReview,
    ) -> None:
        existing_extra_data = (
            assistant_message.extra_data
            if isinstance(
                assistant_message.extra_data,
                dict,
            )
            else {}
        )

        assistant_message.extra_data = {
            **existing_extra_data,
            "requires_human_review": True,
            "review_id": str(
                human_review.id
            ),
            "review_status": human_review.status,
            "review_reason": human_review.reason,
            "requested_action": (
                human_review.requested_action
            ),
        }

        await session.commit()
        await session.refresh(
            assistant_message,
        )

    @staticmethod
    def _build_message_metadata(
        *,
        orchestrator_result: OrchestratorResult,
        streamed: bool,
    ) -> dict[str, Any]:
        return {
            "provider": orchestrator_result.provider,
            "model": orchestrator_result.model,
            "workflow": "langgraph",
            "route": orchestrator_result.route,
            "planner_reason": (
                orchestrator_result.planner_reason
            ),
            "usage": orchestrator_result.usage,
            "streamed": streamed,
            "requires_human_review": (
                orchestrator_result.requires_human_review
            ),
            "review_status": (
                orchestrator_result.review_status
            ),
            "review_reason": (
                orchestrator_result.review_reason
            ),
            "requested_action": (
                orchestrator_result.requested_action
            ),
        }

    @staticmethod
    def _build_streamed_result(
        workflow_data: dict[str, Any],
    ) -> OrchestratorResult:
        response_content = ChatService._required_string(
            workflow_data,
            "response_content",
            (
                "The streamed agent workflow returned "
                "an empty response."
            ),
        )

        model = ChatService._required_string(
            workflow_data,
            "model",
            (
                "The streamed agent workflow returned "
                "no model name."
            ),
        )

        provider = ChatService._required_string(
            workflow_data,
            "provider",
            (
                "The streamed agent workflow returned "
                "no provider name."
            ),
        )

        route = ChatService._required_string(
            workflow_data,
            "route",
            (
                "The streamed planner returned no route."
            ),
        )

        planner_reason = ChatService._required_string(
            workflow_data,
            "planner_reason",
            (
                "The streamed planner returned no "
                "routing reason."
            ),
        )

        usage = workflow_data.get(
            "usage",
            {},
        )

        if not isinstance(usage, dict):
            usage = {}

        action_payload = workflow_data.get(
            "action_payload",
        )

        if not isinstance(action_payload, dict):
            action_payload = None

        return OrchestratorResult(
            response_content=response_content,
            model=model,
            provider=provider,
            route=route,
            planner_reason=planner_reason,
            usage=usage,
            requires_human_review=bool(
                workflow_data.get(
                    "requires_human_review",
                    False,
                )
            ),
            review_status=ChatService._optional_string(
                workflow_data.get(
                    "review_status",
                )
            ),
            review_reason=ChatService._optional_string(
                workflow_data.get(
                    "review_reason",
                )
            ),
            review_id=ChatService._optional_string(
                workflow_data.get(
                    "review_id",
                )
            ),
            requested_action=(
                ChatService._optional_string(
                    workflow_data.get(
                        "requested_action",
                    )
                )
            ),
            request_content=ChatService._optional_string(
                workflow_data.get(
                    "request_content",
                )
            ),
            action_payload=action_payload,
            reviewed_by=ChatService._optional_string(
                workflow_data.get(
                    "reviewed_by",
                )
            ),
            reviewed_at=ChatService._optional_string(
                workflow_data.get(
                    "reviewed_at",
                )
            ),
            reviewer_feedback=(
                ChatService._optional_string(
                    workflow_data.get(
                        "reviewer_feedback",
                    )
                )
            ),
        )

    @staticmethod
    def _required_string(
        data: dict[str, Any],
        key: str,
        error_message: str,
    ) -> str:
        value = str(
            data.get(
                key,
                "",
            )
            or ""
        ).strip()

        if not value:
            raise LLMInvalidResponseError(
                error_message
            )

        return value

    @staticmethod
    def _optional_string(
        value: Any,
    ) -> str | None:
        if value is None:
            return None

        normalized_value = str(
            value
        ).strip()

        if not normalized_value:
            return None

        return normalized_value

    @staticmethod
    async def _store_failed_response(
        *,
        session: AsyncSession,
        conversation: Conversation,
    ) -> None:
        try:
            await session.rollback()

            await MessageService.create_internal_message(
                session=session,
                conversation=conversation,
                role=MessageRole.ASSISTANT,
                content=(
                    "The AI workflow could not generate "
                    "a response."
                ),
                status=MessageStatus.FAILED,
                agent_name="orchestrator",
                extra_data={
                    "provider": "ollama",
                    "model": settings.ollama_model,
                    "workflow": "langgraph",
                },
                commit=True,
            )

        except Exception:
            await session.rollback()