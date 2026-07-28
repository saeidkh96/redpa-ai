import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.schemas.conversation import ConversationCreate, ConversationUpdate


class ConversationService:
    @staticmethod
    async def create(
        session: AsyncSession,
        user_id: uuid.UUID,
        conversation_data: ConversationCreate,
    ) -> Conversation:
        title = conversation_data.title

        if title is None:
            title = "New conversation"
        else:
            title = title.strip()

        conversation = Conversation(
            user_id=user_id,
            title=title,
        )

        session.add(conversation)

        await session.commit()
        await session.refresh(conversation)

        return conversation

    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Conversation | None:
        statement = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )

        result = await session.execute(statement)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_for_user(
        session: AsyncSession,
        user_id: uuid.UUID,
        limit: int,
        offset: int,
    ) -> tuple[list[Conversation], int]:
        statement = (
            select(Conversation)
            .where(
                Conversation.user_id == user_id,
            )
            .order_by(
                Conversation.updated_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        count_statement = (
            select(func.count())
            .select_from(Conversation)
            .where(
                Conversation.user_id == user_id,
            )
        )

        result = await session.execute(statement)
        count_result = await session.execute(count_statement)

        conversations = list(result.scalars().all())
        total = count_result.scalar_one()

        return conversations, total

    @staticmethod
    async def update(
        session: AsyncSession,
        conversation: Conversation,
        conversation_data: ConversationUpdate,
    ) -> Conversation:
        conversation.title = conversation_data.title.strip()
        conversation.updated_at = datetime.now(timezone.utc)

        await session.commit()
        await session.refresh(conversation)

        return conversation

    @staticmethod
    async def touch(
        session: AsyncSession,
        conversation: Conversation,
    ) -> Conversation:
        conversation.updated_at = datetime.now(timezone.utc)

        await session.flush()

        return conversation

    @staticmethod
    async def delete(
        session: AsyncSession,
        conversation: Conversation,
    ) -> None:
        await session.delete(conversation)
        await session.commit()