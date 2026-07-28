import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.message import (
    Message,
    MessageRole,
    MessageStatus,
)


class MessageService:
    @staticmethod
    async def create_user_message(
        session: AsyncSession,
        conversation: Conversation,
        content: str,
        commit: bool = True,
    ) -> Message:
        message = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER.value,
            content=content.strip(),
            status=MessageStatus.COMPLETED.value,
        )

        conversation.updated_at = datetime.now(timezone.utc)

        session.add(message)

        if commit:
            await session.commit()
            await session.refresh(message)
        else:
            await session.flush()

        return message

    @staticmethod
    async def create_internal_message(
        session: AsyncSession,
        conversation: Conversation,
        role: MessageRole,
        content: str,
        status: MessageStatus = MessageStatus.COMPLETED,
        agent_name: str | None = None,
        tool_name: str | None = None,
        extra_data: dict[str, Any] | None = None,
        commit: bool = True,
    ) -> Message:
        message = Message(
            conversation_id=conversation.id,
            role=role.value,
            content=content.strip(),
            status=status.value,
            agent_name=agent_name,
            tool_name=tool_name,
            extra_data=extra_data,
        )

        conversation.updated_at = datetime.now(timezone.utc)

        session.add(message)

        if commit:
            await session.commit()
            await session.refresh(message)
        else:
            await session.flush()

        return message

    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        message_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> Message | None:
        statement = select(Message).where(
            Message.id == message_id,
            Message.conversation_id == conversation_id,
        )

        result = await session.execute(statement)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_for_conversation(
        session: AsyncSession,
        conversation_id: uuid.UUID,
        limit: int,
        offset: int,
    ) -> tuple[list[Message], int]:
        statement = (
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
            )
            .order_by(
                Message.created_at.asc(),
            )
            .limit(limit)
            .offset(offset)
        )

        count_statement = (
            select(func.count())
            .select_from(Message)
            .where(
                Message.conversation_id == conversation_id,
            )
        )

        result = await session.execute(statement)
        count_result = await session.execute(count_statement)

        messages = list(result.scalars().all())
        total = count_result.scalar_one()

        return messages, total

    @staticmethod
    async def get_recent_for_llm(
        session: AsyncSession,
        conversation_id: uuid.UUID,
        limit: int,
    ) -> list[Message]:
        statement = (
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.status
                == MessageStatus.COMPLETED.value,
                Message.role.in_(
                    [
                        MessageRole.USER.value,
                        MessageRole.ASSISTANT.value,
                        MessageRole.SYSTEM.value,
                    ]
                ),
            )
            .order_by(
                Message.created_at.desc(),
            )
            .limit(limit)
        )

        result = await session.execute(statement)

        messages = list(result.scalars().all())

        messages.reverse()

        return messages

    @staticmethod
    async def update_status(
        session: AsyncSession,
        message: Message,
        status: MessageStatus,
    ) -> Message:
        message.status = status.value

        await session.commit()
        await session.refresh(message)

        return message