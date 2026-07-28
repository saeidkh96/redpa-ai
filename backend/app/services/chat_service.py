import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.ollama_client import ollama_client
from app.core.config import settings
from app.core.exceptions import LLMServiceError
from app.models.conversation import Conversation
from app.models.message import (
    Message,
    MessageRole,
    MessageStatus,
)
from app.schemas.ollama import OllamaChatMessage
from app.services.message_service import MessageService


SYSTEM_PROMPT = """
You are RedPA, an enterprise agentic AI assistant.

Your responsibilities:
- Answer clearly and accurately.
- Use the available conversation context.
- Do not claim to have used tools unless a tool result is provided.
- Do not invent sources, database results, files, or external actions.
- State uncertainty when necessary.
- Keep answers practical and structured.
""".strip()


class ChatService:
    @staticmethod
    async def generate_response(
        session: AsyncSession,
        conversation: Conversation,
        content: str,
    ) -> tuple[Message, Message, str]:
        user_message = await MessageService.create_user_message(
            session=session,
            conversation=conversation,
            content=content,
            commit=False,
        )

        await session.commit()
        await session.refresh(user_message)

        history = await MessageService.get_recent_for_llm(
            session=session,
            conversation_id=conversation.id,
            limit=settings.ollama_max_context_messages,
        )

        ollama_messages = ChatService._build_ollama_messages(
            history=history,
        )

        try:
            ollama_response = await ollama_client.chat(
                messages=ollama_messages,
            )

        except LLMServiceError:
            failed_message = await MessageService.create_internal_message(
                session=session,
                conversation=conversation,
                role=MessageRole.ASSISTANT,
                content=(
                    "The AI service could not generate a response."
                ),
                status=MessageStatus.FAILED,
                agent_name="chat-agent",
                extra_data={
                    "provider": "ollama",
                    "model": settings.ollama_model,
                },
                commit=True,
            )

            raise

        assistant_message = (
            await MessageService.create_internal_message(
                session=session,
                conversation=conversation,
                role=MessageRole.ASSISTANT,
                content=ollama_response.message.content,
                status=MessageStatus.COMPLETED,
                agent_name="chat-agent",
                extra_data={
                    "provider": "ollama",
                    "model": ollama_response.model,
                    "done": ollama_response.done,
                    "usage": {
                        "prompt_eval_count": (
                            ollama_response.prompt_eval_count
                        ),
                        "eval_count": (
                            ollama_response.eval_count
                        ),
                        "total_duration": (
                            ollama_response.total_duration
                        ),
                    },
                },
                commit=True,
            )
        )

        return (
            user_message,
            assistant_message,
            ollama_response.model,
        )

    @staticmethod
    def _build_ollama_messages(
        history: list[Message],
    ) -> list[OllamaChatMessage]:
        messages = [
            OllamaChatMessage(
                role="system",
                content=SYSTEM_PROMPT,
            )
        ]

        for message in history:
            if message.role not in {
                MessageRole.USER.value,
                MessageRole.ASSISTANT.value,
                MessageRole.SYSTEM.value,
            }:
                continue

            messages.append(
                OllamaChatMessage(
                    role=message.role,
                    content=message.content,
                )
            )

        return messages