from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from app.api.dependencies import (
    CurrentUser,
    DatabaseSession,
)
from app.core.exceptions import (
    LLMConnectionError,
    LLMInvalidResponseError,
    LLMTimeoutError,
)
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
)
from app.schemas.message import MessageResponse
from app.services.chat_service import ChatService
from app.services.conversation_service import (
    ConversationService,
)


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a message to the AI assistant",
)
async def chat(
    chat_data: ChatRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> ChatResponse:
    conversation = await ConversationService.get_by_id(
        session=session,
        conversation_id=chat_data.conversation_id,
        user_id=current_user.id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    try:
        (
            user_message,
            assistant_message,
            model,
        ) = await ChatService.generate_response(
            session=session,
            conversation=conversation,
            content=chat_data.content,
        )

    except LLMConnectionError as exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exception),
        ) from exception

    except LLMTimeoutError as exception:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exception),
        ) from exception

    except LLMInvalidResponseError as exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exception),
        ) from exception

    return ChatResponse(
        conversation_id=conversation.id,
        user_message=MessageResponse.model_validate(
            user_message,
        ),
        assistant_message=MessageResponse.model_validate(
            assistant_message,
        ),
        model=model,
    )