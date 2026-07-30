from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)
from fastapi.responses import StreamingResponse

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


def _format_sse_event(
    *,
    event: str,
    data: dict[str, Any],
) -> str:
    serialized_data = json.dumps(
        data,
        ensure_ascii=False,
        default=str,
    )

    return (
        f"event: {event}\n"
        f"data: {serialized_data}\n\n"
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


@router.post(
    "/stream",
    status_code=status.HTTP_200_OK,
    summary="Stream a response from the AI assistant",
    response_class=StreamingResponse,
)
async def stream_chat(
    chat_data: ChatRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> StreamingResponse:
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

    async def event_generator() -> AsyncIterator[str]:
        try:
            async for stream_event in ChatService.stream_response(
                session=session,
                conversation=conversation,
                content=chat_data.content,
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

                yield _format_sse_event(
                    event=event_name,
                    data=event_data,
                )

        except LLMConnectionError as exception:
            yield _format_sse_event(
                event="error",
                data={
                    "type": "connection_error",
                    "message": str(exception),
                    "status_code": (
                        status.HTTP_503_SERVICE_UNAVAILABLE
                    ),
                },
            )

        except LLMTimeoutError as exception:
            yield _format_sse_event(
                event="error",
                data={
                    "type": "timeout_error",
                    "message": str(exception),
                    "status_code": (
                        status.HTTP_504_GATEWAY_TIMEOUT
                    ),
                },
            )

        except LLMInvalidResponseError as exception:
            yield _format_sse_event(
                event="error",
                data={
                    "type": "invalid_response_error",
                    "message": str(exception),
                    "status_code": (
                        status.HTTP_502_BAD_GATEWAY
                    ),
                },
            )

        except Exception as exception:
            yield _format_sse_event(
                event="error",
                data={
                    "type": "internal_error",
                    "message": str(exception),
                    "status_code": (
                        status.HTTP_500_INTERNAL_SERVER_ERROR
                    ),
                },
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )