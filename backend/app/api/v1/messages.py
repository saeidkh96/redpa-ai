import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.schemas.message import (
    MessageCreate,
    MessageListResponse,
    MessageResponse,
)
from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService


router = APIRouter(
    prefix="/conversations/{conversation_id}/messages",
    tags=["Messages"],
)


@router.post(
    "",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user message",
)
async def create_message(
    conversation_id: uuid.UUID,
    message_data: MessageCreate,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> MessageResponse:
    conversation = await ConversationService.get_by_id(
        session=session,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    message = await MessageService.create_user_message(
        session=session,
        conversation=conversation,
        content=message_data.content,
    )

    return MessageResponse.model_validate(message)


@router.get(
    "",
    response_model=MessageListResponse,
    status_code=status.HTTP_200_OK,
    summary="List messages in a conversation",
)
async def list_messages(
    conversation_id: uuid.UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=200,
            description="Maximum number of messages to return.",
        ),
    ] = 50,
    offset: Annotated[
        int,
        Query(
            ge=0,
            description="Number of messages to skip.",
        ),
    ] = 0,
) -> MessageListResponse:
    conversation = await ConversationService.get_by_id(
        session=session,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    messages, total = await MessageService.get_all_for_conversation(
        session=session,
        conversation_id=conversation.id,
        limit=limit,
        offset=offset,
    )

    return MessageListResponse(
        items=[
            MessageResponse.model_validate(message)
            for message in messages
        ],
        total=total,
        limit=limit,
        offset=offset,
    )