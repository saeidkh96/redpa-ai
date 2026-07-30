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
from app.models.message import (
    Message,
    MessageRole,
    MessageStatus,
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

        except LLMServiceError:
            await ChatService._store_failed_response(
                session=session,
                conversation=conversation,
            )

            raise

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
                extra_data={
                    "provider": (
                        orchestrator_result.provider
                    ),
                    "model": (
                        orchestrator_result.model
                    ),
                    "workflow": "langgraph",
                    "route": (
                        orchestrator_result.route
                    ),
                    "planner_reason": (
                        orchestrator_result.planner_reason
                    ),
                    "usage": (
                        orchestrator_result.usage
                    ),
                    "streamed": False,
                },
                commit=True,
            )
        )

        return (
            user_message,
            assistant_message,
            orchestrator_result.model,
        )

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

            response_content = str(
                workflow_completed_data.get(
                    "response_content",
                    "",
                )
                or ""
            ).strip()

            model = str(
                workflow_completed_data.get(
                    "model",
                    "",
                )
                or ""
            ).strip()

            provider = str(
                workflow_completed_data.get(
                    "provider",
                    "",
                )
                or ""
            ).strip()

            route = str(
                workflow_completed_data.get(
                    "route",
                    "",
                )
                or ""
            ).strip()

            planner_reason = str(
                workflow_completed_data.get(
                    "planner_reason",
                    "",
                )
                or ""
            ).strip()

            usage = workflow_completed_data.get(
                "usage",
                {},
            )

            if not isinstance(usage, dict):
                usage = {}

            if not response_content:
                raise LLMInvalidResponseError(
                    "The streamed agent workflow returned "
                    "an empty response."
                )

            if not model:
                raise LLMInvalidResponseError(
                    "The streamed agent workflow returned "
                    "no model name."
                )

            if not provider:
                raise LLMInvalidResponseError(
                    "The streamed agent workflow returned "
                    "no provider name."
                )

            if not route:
                raise LLMInvalidResponseError(
                    "The streamed planner returned no route."
                )

            if not planner_reason:
                raise LLMInvalidResponseError(
                    "The streamed planner returned no "
                    "routing reason."
                )

            assistant_message = (
                await MessageService.create_internal_message(
                    session=session,
                    conversation=conversation,
                    role=MessageRole.ASSISTANT,
                    content=response_content,
                    status=MessageStatus.COMPLETED,
                    agent_name="orchestrator",
                    extra_data={
                        "provider": provider,
                        "model": model,
                        "workflow": "langgraph",
                        "route": route,
                        "planner_reason": planner_reason,
                        "usage": usage,
                        "streamed": True,
                    },
                    commit=True,
                )
            )

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
                        response_content
                    ),
                    "model": model,
                    "provider": provider,
                    "route": route,
                    "planner_reason": (
                        planner_reason
                    ),
                    "usage": usage,
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