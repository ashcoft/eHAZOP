"""Knowledge base and RAG schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class KnowledgeChunkBase(BaseModel):
    """Base knowledge chunk schema."""
    content: str = Field(min_length=1)
    source_reference: str | None = None
    metadata: dict[str, Any] | None = None


class KnowledgeChunkCreate(KnowledgeChunkBase):
    """Knowledge chunk creation schema."""
    document_id: str
    chunk_index: int
    chunk_size: int


class KnowledgeChunkResponse(BaseModel):
    """Knowledge chunk response schema."""
    id: str
    document_id: str
    content: str
    chunk_index: int
    chunk_size: int
    source_reference: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentBase(BaseModel):
    """Base document schema."""
    name: str = Field(min_length=1, max_length=255)
    document_type: str = Field(min_length=1, max_length=100)
    description: str | None = None
    version: str | None = None
    discipline: str | None = None
    is_confidential: bool = False


class DocumentCreate(DocumentBase):
    """Document creation schema."""
    study_id: str | None = None
    file_path: str
    file_name: str
    file_size: int
    file_mime_type: str


class DocumentResponse(BaseModel):
    """Document response schema."""
    id: str
    study_id: str | None
    name: str
    document_type: str
    description: str | None
    file_path: str
    file_name: str
    file_size: int
    file_mime_type: str
    storage_backend: str
    version: str | None
    discipline: str | None
    is_confidential: bool
    uploaded_by_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """Paginated document list response."""
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int


class KnowledgeSearchRequest(BaseModel):
    """Knowledge search request."""
    query: str = Field(min_length=1)
    study_id: str | None = None
    document_ids: list[str] | None = None
    limit: int = Field(default=10, ge=1, le=100)
    similarity_threshold: float = Field(default=0.7, ge=0, le=1)


class KnowledgeSearchResult(BaseModel):
    """Knowledge search result."""
    chunk: KnowledgeChunkResponse
    document: DocumentResponse | None = None
    similarity_score: float
    highlights: list[str] = []


class KnowledgeSearchResponse(BaseModel):
    """Knowledge search response."""
    results: list[KnowledgeSearchResult]
    total: int
    query: str


class DocumentIngestRequest(BaseModel):
    """Document ingestion request."""
    study_id: str | None = None
    document_type: str = Field(min_length=1, max_length=100)
    description: str | None = None
    version: str | None = None
    discipline: str | None = None
    chunk_size: int = Field(default=500, ge=100, le=2000)
    chunk_overlap: int = Field(default=50, ge=0, le=500)


class CitationResponse(BaseModel):
    """Citation response schema."""
    id: str
    chunk_id: str
    suggestion_id: str | None
    relevance_score: float | None
    created_at: datetime

    model_config = {"from_attributes": True}"