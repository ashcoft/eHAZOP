"""File storage abstraction service."""

import hashlib
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.document import Document

settings = get_settings()


class StorageService:
    """Abstraction for file storage (local, S3, MinIO)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def upload_file(
        self,
        content: bytes,
        filename: str,
        file_type: str,
        study_id: str | None = None,
        document_type: str = "report",
        mime_type: str = "application/octet-stream",
        is_confidential: bool = False,
        uploaded_by_id: str | None = None,
    ) -> dict[str, Any]:
        """Upload a file to storage."""
        # Generate unique file path
        file_id = str(uuid.uuid4())
        date_str = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        
        if settings.STORAGE_TYPE == "local":
            return await self._upload_local(
                content, filename, file_id, date_str, file_type, study_id,
                document_type, mime_type, is_confidential, uploaded_by_id
            )
        elif settings.STORAGE_TYPE in ["s3", "minio"]:
            return await self._upload_s3(
                content, filename, file_id, date_str, file_type, study_id,
                document_type, mime_type, is_confidential, uploaded_by_id
            )
        else:
            raise ValueError(f"Unsupported storage type: {settings.STORAGE_TYPE}")

    async def _upload_local(
        self,
        content: bytes,
        filename: str,
        file_id: str,
        date_str: str,
        file_type: str,
        study_id: str | None,
        document_type: str,
        mime_type: str,
        is_confidential: bool,
        uploaded_by_id: str | None,
    ) -> dict[str, Any]:
        """Upload file to local storage."""
        # Sanitize filename to prevent path traversal attacks
        safe_filename = os.path.basename(filename)
        safe_filename = re.sub(r"[^A-Za-z0-9._-]", "_", safe_filename)
        if (
            not safe_filename
            or safe_filename in {".", ".."}
            or safe_filename.startswith(".")
        ):
            safe_filename = f"file_{file_id}"

        base_storage_root = os.path.realpath(settings.STORAGE_LOCAL_PATH)
        storage_path = os.path.realpath(os.path.join(base_storage_root, date_str))
        if os.path.commonpath([base_storage_root, storage_path]) != base_storage_root:
            raise ValueError("Invalid storage path")
        os.makedirs(storage_path, exist_ok=True)

        file_path = os.path.realpath(os.path.join(storage_path, f"{file_id}_{safe_filename}"))
        if os.path.commonpath([base_storage_root, file_path]) != base_storage_root:
            raise ValueError("Invalid file path")

        with open(file_path, "wb") as f:
            f.write(content)

        # Create document record
        document = Document(
            study_id=study_id,
            name=filename,
            document_type=document_type,
            file_path=file_path,
            file_name=filename,
            file_size=len(content),
            file_mime_type=mime_type,
            storage_backend="local",
            is_confidential=is_confidential,
            uploaded_by_id=uploaded_by_id or "system",
        )
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)

        return {
            "document_id": document.id,
            "file_path": file_path,
            "file_name": filename,
            "file_size": len(content),
            "storage_backend": "local",
        }

    async def _upload_s3(
        self,
        content: bytes,
        filename: str,
        file_id: str,
        date_str: str,
        file_type: str,
        study_id: str | None,
        document_type: str,
        mime_type: str,
        is_confidential: bool,
        uploaded_by_id: str | None,
    ) -> dict[str, Any]:
        """Upload file to S3/MinIO storage."""
        # For S3/MinIO, would use boto3
        # This is a placeholder implementation
        bucket_path = f"{date_str}/{file_id}_{filename}"
        
        # In production, use boto3 to upload to S3/MinIO
        # For now, just create the document record
        document = Document(
            study_id=study_id,
            name=filename,
            document_type=document_type,
            file_path=bucket_path,
            file_name=filename,
            file_size=len(content),
            file_mime_type=mime_type,
            storage_backend=settings.STORAGE_TYPE,
            is_confidential=is_confidential,
            uploaded_by_id=uploaded_by_id or "system",
        )
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)

        return {
            "document_id": document.id,
            "file_path": bucket_path,
            "file_name": filename,
            "file_size": len(content),
            "storage_backend": settings.STORAGE_TYPE,
        }

    async def download_file(self, document_id: str) -> bytes | None:
        """Download a file from storage."""
        result = await self.db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()
        if not document:
            return None

        if document.storage_backend == "local":
            try:
                with open(document.file_path, "rb") as f:
                    return f.read()
            except Exception:
                return None
        elif document.storage_backend in ["s3", "minio"]:
            # Would use boto3 to download
            return None

        return None

    async def get_signed_url(
        self,
        document_id: str,
        expires_in: int = 3600,
    ) -> str | None:
        """Generate a signed URL for file download."""
        result = await self.db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()
        if not document:
            return None

        if document.storage_backend == "local":
            # For local storage, return a simple path or generate signed token
            return f"/api/v1/documents/{document_id}/download"
        elif document.storage_backend in ["s3", "minio"]:
            # Would generate pre-signed URL using boto3
            return None

        return None

    async def delete_file(self, document_id: str) -> bool:
        """Delete a file from storage."""
        result = await self.db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()
        if not document:
            return False

        if document.storage_backend == "local":
            try:
                if os.path.exists(document.file_path):
                    os.remove(document.file_path)
            except Exception:
                pass

        await self.db.delete(document)
        await self.db.flush()
        return True

    async def list_documents(
        self,
        study_id: str | None = None,
        document_type: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Document], int]:
        """List documents with filters."""
        query = select(Document)
        
        if study_id:
            query = query.where(Document.study_id == study_id)
        if document_type:
            query = query.where(Document.document_type == document_type)

        from sqlalchemy import func
        count_query = select(func.count(Document.id))
        if study_id:
            count_query = count_query.where(Document.study_id == study_id)
        if document_type:
            count_query = count_query.where(Document.document_type == document_type)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Document.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        documents = list(result.scalars().all())

        return documents, total