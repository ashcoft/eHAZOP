"""Knowledge base and RAG models."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ehazop_backend.app.core.database import Base


class KnowledgeChunk(Base):
    """Chunked content from documents for RAG retrieval."""

    __tablename__ = "knowledge_chunks"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    document_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("documents.id"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )  # Order in document
    chunk_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )  # Character count
    source_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )  # e.g., "Page 5", "Section 4.2"
    metadata: Mapped[dict | None] = mapped_column(
        nullable=True,
    )  # Additional metadata (JSON)
    # Vector embedding - will be managed separately with pgvector
    # embedding stored as a separate table or JSON column for portability
    embedding_dimension: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow(),
    )

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="knowledge_chunks")
    citations: Mapped[list["Citation"]] = relationship(
        "Citation",
        back_populates="chunk",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<KnowledgeChunk {self.id} (index: {self.chunk_index})>"


class Citation(Base):
    """Citation linking LLM suggestions to knowledge chunks."""

    __tablename__ = "citations"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    chunk_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("knowledge_chunks.id"),
        nullable=False,
    )
    suggestion_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("llm_suggestions.id"),
        nullable=True,
    )  # Link to LLM suggestion
    relevance_score: Mapped[float | None] = mapped_column(
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow(),
    )

    # Relationships
    chunk: Mapped["KnowledgeChunk"] = relationship("KnowledgeChunk", back_populates="citations")


# Import Document and LLMSuggestion for relationships
from ehazop_backend.app.models.document import Document
from ehazop_backend.app.models.hazard import LLMSuggestion


class EmbeddingIndex(Base):
    """Embedding index metadata for vector operations."""

    __tablename__ = "embedding_indexes"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )  # e.g., "text-embedding-004"
    dimension: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    index_type: Mapped[str] = mapped_column(
        String(50),
        default="hnsw",
        nullable=False,
    )  # hnsw, ivfflat
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        default=True,
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

    def __repr__(self) -> str:
        return f"<EmbeddingIndex {self.name}>"