from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import LLMServiceError
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
        user_message = (
            await MessageService.create_user_message(
                session=session,
                conversation=conversation,
                content=content,
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
            await MessageService.create_internal_message(
                session=session,
                conversation=conversation,
                role=MessageRole.ASSISTANT,
                content=(
                    "The AI workflow could not generate a response."
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
                agent_name="chat-agent",
                extra_data={
                    "provider": (
                        orchestrator_result.provider
                    ),
                    "model": orchestrator_result.model,
                    "workflow": "langgraph",
                    "route": orchestrator_result.route,
                    "planner_reason": (
                        orchestrator_result.planner_reason
                    ),
                    "usage": (
                        orchestrator_result.usage
                    ),
                },
                commit=True,
            )
        )

        return (
            user_message,
            assistant_message,
            orchestrator_result.model,
        )