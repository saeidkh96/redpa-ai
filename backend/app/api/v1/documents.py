import logging
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
    status,
)

from app.api.dependencies import (
    CurrentUser,
    DatabaseSession,
)
from app.schemas.document import DocumentResponse
from app.services.conversation_service import ConversationService
from app.services.document_service import DocumentService


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document",
)
async def upload_document(
    current_user: CurrentUser,
    session: DatabaseSession,
    file: Annotated[
        UploadFile,
        File(
            description="PDF, TXT, Markdown, or DOCX document",
        ),
    ],
    conversation_id: Annotated[
        UUID | None,
        Form(),
    ] = None,
) -> DocumentResponse:
    user_id = current_user.id

    if conversation_id is not None:
        conversation = await ConversationService.get_by_id(
            session=session,
            conversation_id=conversation_id,
            user_id=user_id,
        )

        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )

    service = DocumentService(session)

    try:
        document = await service.upload_document(
            file=file,
            user_id=user_id,
            conversation_id=conversation_id,
        )

        return DocumentResponse.model_validate(document)

    except ValueError as exception:
        logger.warning(
            "Document validation failed for user %s: %s",
            user_id,
            exception,
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exception),
        ) from exception

    except Exception as exception:
        await session.rollback()

        logger.exception(
            "Document upload failed for user %s",
            user_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document upload failed.",
        ) from exception


@router.get(
    "",
    response_model=list[DocumentResponse],
    status_code=status.HTTP_200_OK,
    summary="List the current user's documents",
)
async def list_documents(
    current_user: CurrentUser,
    session: DatabaseSession,
) -> list[DocumentResponse]:
    service = DocumentService(session)

    documents = await service.get_user_documents(
        user_id=current_user.id,
    )

    return [
        DocumentResponse.model_validate(document)
        for document in documents
    ]


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a document",
)
async def get_document(
    document_id: UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> DocumentResponse:
    service = DocumentService(session)

    document = await service.get_document(
        document_id=document_id,
        user_id=current_user.id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return DocumentResponse.model_validate(document)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document",
)
async def delete_document(
    document_id: UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> Response:
    service = DocumentService(session)

    deleted = await service.delete_document(
        document_id=document_id,
        user_id=current_user.id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )