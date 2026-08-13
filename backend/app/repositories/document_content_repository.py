from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_content import DocumentContent


class DocumentContentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        document_id: UUID,
        text: str,
        page_count: int,
        content_metadata: dict,
    ) -> DocumentContent:
        document_content = DocumentContent(
            document_id=document_id,
            text=text,
            page_count=page_count,
            content_metadata=content_metadata,
        )

        self.session.add(document_content)

        try:
            await self.session.commit()
            await self.session.refresh(document_content)
        except Exception:
            await self.session.rollback()
            raise

        return document_content

    async def get_by_document_id(
        self,
        document_id: UUID,
    ) -> DocumentContent | None:
        result = await self.session.execute(
            select(DocumentContent).where(
                DocumentContent.document_id == document_id,
            )
        )

        return result.scalar_one_or_none()

    async def delete(
        self,
        document_content: DocumentContent,
    ) -> None:
        await self.session.delete(document_content)

        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise