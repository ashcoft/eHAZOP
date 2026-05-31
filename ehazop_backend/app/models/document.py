"""Document and file storage models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Document(Base):
    """Document metadata (P&IDs, PFDs, single-line diagrams, past HAZOPs)."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    study_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("studies.id"),
        nullable=True,
    )  # Optional: link to specific study
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    document_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )  # pid, pfd, single_line_diagram, hazop_report, procedure, other
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )  # Storage path
    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    file_size: Mapped[int] = mapped_column(
        nullable=False,
    )  # Bytes
    file_mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    storage_backend: Mapped[str] = mapped_column(
        String(50),
        default="local",
        nullable=False,
    )  # local, s3, minio
    version: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
    )  # Document revision
    discipline: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )  # electrical, process, instrumentation, etc.
    is_confidential: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    uploaded_by_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
    )

    # Relationships
    study: Mapped["Study | None"] = relationship("Study", back_populates="documents")
    uploaded_by: Mapped["User"] = relationship("User")
    knowledge_chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        "KnowledgeChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Document {self.name}>"


# Import Study and User for relationships
from app.models.user import Study, User