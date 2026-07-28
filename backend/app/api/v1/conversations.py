import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.schemas.conversation import (
    ConversationCreate,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdate,
)
from app.services.conversation_service import ConversationService


router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a conversation",
)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> ConversationResponse:
    conversation = await ConversationService.create(
        session=session,
        user_id=current_user.id,
        conversation_data=conversation_data,
    )

    return ConversationResponse.model_validate(conversation)


@router.get(
    "",
    response_model=ConversationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List current user's conversations",
)
async def list_conversations(
    current_user: CurrentUser,
    session: DatabaseSession,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
            description="Maximum number of conversations to return.",
        ),
    ] = 20,
    offset: Annotated[
        int,
        Query(
            ge=0,
            description="Number of conversations to skip.",
        ),
    ] = 0,
) -> ConversationListResponse:
    conversations, total = await ConversationService.get_all_for_user(
        session=session,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )

    return ConversationListResponse(
        items=[
            ConversationResponse.model_validate(conversation)
            for conversation in conversations
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a conversation",
)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> ConversationResponse:
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

    return ConversationResponse.model_validate(conversation)


@router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a conversation",
)
async def update_conversation(
    conversation_id: uuid.UUID,
    conversation_data: ConversationUpdate,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> ConversationResponse:
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

    updated_conversation = await ConversationService.update(
        session=session,
        conversation=conversation,
        conversation_data=conversation_data,
    )

    return ConversationResponse.model_validate(updated_conversation)


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a conversation",
)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> Response:
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

    await ConversationService.delete(
        session=session,
        conversation=conversation,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )