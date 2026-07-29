import asyncio
import re
import uuid
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import (
    Document,
    DocumentSource,
    DocumentStatus,
)
from app.repositories.document_chunk_repository import (
    DocumentChunkRepository,
)
from app.repositories.document_content_repository import (
    DocumentContentRepository,
)
from app.repositories.document_repository import DocumentRepository
from app.schemas.extracted_document import ExtractedDocument
from app.services.chunking_service import ChunkingService
from app.services.document_extractor import DocumentExtractor
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService


class DocumentService:
    MAX_FILE_SIZE = 20 * 1024 * 1024

    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "text/plain",
        "text/markdown",
        (
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
    }

    def __init__(self, db: AsyncSession):
        self.db = db

        self.repository = DocumentRepository(db)
        self.content_repository = DocumentContentRepository(db)
        self.chunk_repository = DocumentChunkRepository(db)

        self.extractor = DocumentExtractor()

        self.chunking_service = ChunkingService(
            chunk_size=1000,
            chunk_overlap=200,
        )

        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStoreService()

        self.upload_directory = Path("storage/uploads")
        self.upload_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    async def upload_document(
        self,
        *,
        file: UploadFile,
        user_id: UUID,
        conversation_id: UUID | None = None,
    ) -> Document:
        filename = self._sanitize_filename(
            file.filename or "document"
        )

        mime_type = (
            file.content_type
            or "application/octet-stream"
        )

        self._validate_mime_type(mime_type)

        generated_document_id = uuid.uuid4()

        user_directory = (
            self.upload_directory / str(user_id)
        )

        user_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        stored_filename = (
            f"{generated_document_id}_{filename}"
        )

        storage_path = (
            user_directory / stored_filename
        )

        document: Document | None = None
        vectors_created = False

        try:
            size_bytes = await self._save_file(
                file=file,
                destination=storage_path,
            )

            document = await self.repository.create(
                user_id=user_id,
                conversation_id=conversation_id,
                filename=filename,
                mime_type=mime_type,
                size_bytes=size_bytes,
                storage_path=str(storage_path),
                source=DocumentSource.UPLOAD,
            )

            document = await self.mark_as_processing(
                document
            )

            extracted_document = (
                await self._extract_document(
                    storage_path
                )
            )

            self._validate_extracted_document(
                extracted_document
            )

            document_content = (
                await self.content_repository.get_by_document_id(
                    document.id
                )
            )

            if document_content is None:
                document_content = (
                    await self.content_repository.create(
                        document_id=document.id,
                        text=extracted_document.text,
                        page_count=(
                            extracted_document.page_count
                        ),
                        content_metadata=(
                            extracted_document.metadata
                        ),
                    )
                )

            existing_chunks = (
                await self.chunk_repository.get_by_content_id(
                    document_content.id
                )
            )

            if not existing_chunks:
                chunk_texts = (
                    self.chunking_service.split_text(
                        document_content.text
                    )
                )

                if not chunk_texts:
                    raise ValueError(
                        "The extracted document could not "
                        "be divided into text chunks."
                    )

                await self.chunk_repository.create_many(
                    document_id=document.id,
                    content_id=document_content.id,
                    chunks=chunk_texts,
                )

                existing_chunks = (
                    await self.chunk_repository.get_by_content_id(
                        document_content.id
                    )
                )

            if not existing_chunks:
                raise ValueError(
                    "No document chunks were created."
                )

            await self._index_document_chunks(
                document=document,
                content_id=document_content.id,
                chunks=existing_chunks,
            )

            vectors_created = True

            document = await self.mark_as_ready(
                document
            )

            return document

        except ValueError as exception:
            if document is None:
                if storage_path.exists():
                    storage_path.unlink()

                raise

            if vectors_created:
                await self._safe_delete_vectors(
                    document.id
                )

            error_message = (
                str(exception).strip()
                or "The document could not be processed."
            )

            document = await self.mark_as_failed(
                document=document,
                error_message=error_message[:1000],
            )

            return document

        except Exception as exception:
            if document is None:
                if storage_path.exists():
                    storage_path.unlink()

                raise

            await self._safe_delete_vectors(
                document.id
            )

            error_message = (
                str(exception).strip()
                or "Document processing failed."
            )

            document = await self.mark_as_failed(
                document=document,
                error_message=error_message[:1000],
            )

            return document

        finally:
            await file.close()

    async def get_document(
        self,
        *,
        document_id: UUID,
        user_id: UUID,
    ) -> Document | None:
        document = await self.repository.get_by_id(
            document_id
        )

        if document is None:
            return None

        if document.user_id != user_id:
            return None

        return document

    async def get_user_documents(
        self,
        *,
        user_id: UUID,
    ) -> list[Document]:
        return await self.repository.get_by_user(
            user_id
        )

    async def delete_document(
        self,
        *,
        document_id: UUID,
        user_id: UUID,
    ) -> bool:
        document = await self.get_document(
            document_id=document_id,
            user_id=user_id,
        )

        if document is None:
            return False

        await self.vector_store.initialize()

        await self.vector_store.delete_document(
            document_id=document.id
        )

        if document.storage_path:
            storage_path = Path(
                document.storage_path
            )

            if storage_path.exists():
                storage_path.unlink()

        await self.repository.delete(document)

        return True

    async def mark_as_processing(
        self,
        document: Document,
    ) -> Document:
        return await self.repository.update_status(
            document=document,
            status=DocumentStatus.PROCESSING,
            error_message=None,
        )

    async def mark_as_ready(
        self,
        document: Document,
    ) -> Document:
        return await self.repository.update_status(
            document=document,
            status=DocumentStatus.READY,
            error_message=None,
        )

    async def mark_as_failed(
        self,
        document: Document,
        error_message: str,
    ) -> Document:
        return await self.repository.update_status(
            document=document,
            status=DocumentStatus.FAILED,
            error_message=error_message,
        )

    async def _index_document_chunks(
        self,
        *,
        document: Document,
        content_id: UUID,
        chunks: list[Any],
    ) -> None:
        await self.vector_store.initialize()

        ordered_chunks = sorted(
            chunks,
            key=lambda chunk: chunk.chunk_index,
        )

        chunk_texts = [
            chunk.text.strip()
            for chunk in ordered_chunks
        ]

        if not chunk_texts:
            raise ValueError(
                "No chunk text was available for embedding."
            )

        if any(
            not chunk_text
            for chunk_text in chunk_texts
        ):
            raise ValueError(
                "One or more document chunks are empty."
            )

        embeddings = (
            await self.embedding_service.embed_texts(
                chunk_texts
            )
        )

        if len(embeddings) != len(ordered_chunks):
            raise RuntimeError(
                "The number of generated embeddings does "
                "not match the number of document chunks."
            )

        vector_chunks: list[dict[str, Any]] = []

        for chunk, embedding in zip(
            ordered_chunks,
            embeddings,
            strict=True,
        ):
            vector_chunks.append(
                {
                    "chunk_id": chunk.id,
                    "document_id": document.id,
                    "content_id": content_id,
                    "user_id": document.user_id,
                    "conversation_id": (
                        document.conversation_id
                    ),
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                    "embedding": embedding,
                    "metadata": {
                        "filename": document.filename,
                        "mime_type": document.mime_type,
                        "source": (
                            document.source.value
                            if hasattr(
                                document.source,
                                "value",
                            )
                            else str(document.source)
                        ),
                    },
                }
            )

        await self.vector_store.add_chunks(
            vector_chunks
        )

    async def _safe_delete_vectors(
        self,
        document_id: UUID,
    ) -> None:
        try:
            await self.vector_store.initialize()

            await self.vector_store.delete_document(
                document_id=document_id
            )

        except Exception:
            pass

    async def _extract_document(
        self,
        storage_path: Path,
    ) -> ExtractedDocument:
        return await asyncio.to_thread(
            self.extractor.extract,
            storage_path,
        )

    async def _save_file(
        self,
        *,
        file: UploadFile,
        destination: Path,
    ) -> int:
        total_size = 0
        chunk_size = 1024 * 1024

        with destination.open("wb") as output_file:
            while chunk := await file.read(
                chunk_size
            ):
                total_size += len(chunk)

                if total_size > self.MAX_FILE_SIZE:
                    output_file.close()

                    if destination.exists():
                        destination.unlink()

                    raise ValueError(
                        "File size exceeds the "
                        "20 MB limit."
                    )

                output_file.write(chunk)

        if total_size == 0:
            if destination.exists():
                destination.unlink()

            raise ValueError(
                "The uploaded file is empty."
            )

        return total_size

    def _validate_mime_type(
        self,
        mime_type: str,
    ) -> None:
        if mime_type not in self.ALLOWED_MIME_TYPES:
            raise ValueError(
                f"Unsupported file type: {mime_type}"
            )

    @staticmethod
    def _validate_extracted_document(
        extracted_document: ExtractedDocument,
    ) -> None:
        if not extracted_document.text.strip():
            raise ValueError(
                "No readable text was found "
                "in the document."
            )

    @staticmethod
    def _sanitize_filename(
        filename: str,
    ) -> str:
        filename = Path(filename).name

        safe_filename = re.sub(
            r"[^a-zA-Z0-9._-]",
            "_",
            filename,
        )

        safe_filename = safe_filename.strip(
            "._"
        )

        if not safe_filename:
            return "document"

        return safe_filename[:255]