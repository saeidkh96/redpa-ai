import re
import uuid
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import (
    Document,
    DocumentSource,
    DocumentStatus,
)
from app.repositories.document_repository import DocumentRepository


class DocumentService:
    MAX_FILE_SIZE = 20 * 1024 * 1024

    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "text/plain",
        "text/markdown",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = DocumentRepository(db)

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

        mime_type = file.content_type or "application/octet-stream"

        self._validate_mime_type(mime_type)

        document_id = uuid.uuid4()

        user_directory = self.upload_directory / str(user_id)

        user_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        stored_filename = f"{document_id}_{filename}"

        storage_path = user_directory / stored_filename

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

            return document

        except Exception:
            if storage_path.exists():
                storage_path.unlink()

            raise

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

        if document.storage_path:
            storage_path = Path(document.storage_path)

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

    async def _save_file(
        self,
        *,
        file: UploadFile,
        destination: Path,
    ) -> int:
        total_size = 0
        chunk_size = 1024 * 1024

        with destination.open("wb") as output_file:
            while chunk := await file.read(chunk_size):
                total_size += len(chunk)

                if total_size > self.MAX_FILE_SIZE:
                    output_file.close()

                    if destination.exists():
                        destination.unlink()

                    raise ValueError(
                        "File size exceeds the 20 MB limit."
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
    def _sanitize_filename(
        filename: str,
    ) -> str:
        filename = Path(filename).name

        safe_filename = re.sub(
            r"[^a-zA-Z0-9._-]",
            "_",
            filename,
        )

        safe_filename = safe_filename.strip("._")

        if not safe_filename:
            return "document"

        return safe_filename[:255]