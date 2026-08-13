from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import (
    Document,
    DocumentSource,
    DocumentStatus,
)


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID | None,
        filename: str,
        mime_type: str,
        size_bytes: int,
        storage_path: str,
        source: DocumentSource = DocumentSource.UPLOAD,
    ) -> Document:
        document = Document(
            user_id=user_id,
            conversation_id=conversation_id,
            filename=filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            storage_path=storage_path,
            source=source,
            status=DocumentStatus.UPLOADING,
        )

        self.session.add(document)

        try:
            await self.session.commit()
            await self.session.refresh(document)
        except Exception:
            await self.session.rollback()
            raise

        return document

    async def get_by_id(
        self,
        document_id: UUID,
    ) -> Document | None:
        result = await self.session.execute(
            select(Document).where(
                Document.id == document_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: UUID,
    ) -> list[Document]:
        result = await self.session.execute(
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
        )

        return list(result.scalars().all())

    async def update_status(
        self,
        document: Document,
        status: DocumentStatus,
        error_message: str | None = None,
    ) -> Document:
        document.status = status
        document.error_message = error_message

        try:
            await self.session.commit()
            await self.session.refresh(document)
        except Exception:
            await self.session.rollback()
            raise

        return document

    async def delete(
        self,
        document: Document,
    ) -> None:
        await self.session.delete(document)

        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise