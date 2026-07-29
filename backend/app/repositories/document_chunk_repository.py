from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_chunk import DocumentChunk


class DocumentChunkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_many(
        self,
        *,
        document_id: UUID,
        content_id: UUID,
        chunks: list[str],
    ) -> list[DocumentChunk]:
        document_chunks = [
            DocumentChunk(
                document_id=document_id,
                content_id=content_id,
                chunk_index=index,
                text=chunk,
                character_count=len(chunk),
            )
            for index, chunk in enumerate(chunks)
        ]

        self.session.add_all(document_chunks)

        try:
            await self.session.commit()

            for document_chunk in document_chunks:
                await self.session.refresh(document_chunk)

        except Exception:
            await self.session.rollback()
            raise

        return document_chunks

    async def get_by_document_id(
        self,
        document_id: UUID,
    ) -> list[DocumentChunk]:
        result = await self.session.execute(
            select(DocumentChunk)
            .where(
                DocumentChunk.document_id == document_id,
            )
            .order_by(DocumentChunk.chunk_index.asc())
        )

        return list(result.scalars().all())

    async def get_by_content_id(
        self,
        content_id: UUID,
    ) -> list[DocumentChunk]:
        result = await self.session.execute(
            select(DocumentChunk)
            .where(
                DocumentChunk.content_id == content_id,
            )
            .order_by(DocumentChunk.chunk_index.asc())
        )

        return list(result.scalars().all())

    async def delete_by_document_id(
        self,
        document_id: UUID,
    ) -> None:
        await self.session.execute(
            delete(DocumentChunk).where(
                DocumentChunk.document_id == document_id,
            )
        )

        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise