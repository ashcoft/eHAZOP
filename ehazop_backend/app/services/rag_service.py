"""RAG (Retrieval-Augmented Generation) knowledge base service."""

from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeChunk, Citation, EmbeddingIndex
from app.models.document import Document


class RAGService:
    """Service for knowledge base ingestion and retrieval."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def ingest_document(
        self,
        document_id: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> list[KnowledgeChunk]:
        """Ingest a document by chunking and creating embeddings."""
        # Get document
        result = await self.db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()
        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Read document content (for text files)
        content = await self._read_document_content(document)
        
        # Chunk content
        chunks = self._chunk_text(content, chunk_size, chunk_overlap)
        
        # Create chunk records
        created_chunks = []
        for index, chunk_text in enumerate(chunks):
            chunk = KnowledgeChunk(
                document_id=document_id,
                content=chunk_text,
                chunk_index=index,
                chunk_size=len(chunk_text),
                source_reference=f"Chunk {index + 1}",
            )
            self.db.add(chunk)
            created_chunks.append(chunk)

        await self.db.flush()
        
        for chunk in created_chunks:
            await self.db.refresh(chunk)
        
        return created_chunks

    async def _read_document_content(self, document: Document) -> str:
        """Read document content based on storage backend."""
        # For local storage, read file content
        if document.storage_backend == "local":
            try:
                with open(document.file_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                return ""
        # Add other storage backends as needed
        return ""

    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> list[str]:
        """Split text into overlapping chunks."""
        if not text:
            return []

        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence/paragraph boundaries
            if end < len(text):
                for sep in ["\n\n", "\n", ". ", " "]:
                    last_sep = chunk.rfind(sep)
                    if last_sep > chunk_size // 2:
                        chunk = chunk[:last_sep]
                        end = start + last_sep + len(sep)
                        break

            chunks.append(chunk.strip())
            start = end - overlap

        return chunks

    async def generate_embeddings(self, chunks: list[KnowledgeChunk]) -> list[list[float]]:
        """Generate embeddings for chunks using LLM service."""
        from app.services.llm_service import LLMService
        
        llm_service = LLMService(self.db)
        embeddings = []
        
        for chunk in chunks:
            try:
                embedding = await llm_service.provider.embed(chunk.content)
                embeddings.append(embedding)
                chunk.embedding_dimension = len(embedding)
            except Exception:
                embeddings.append([])
        
        await self.db.flush()
        return embeddings

    async def search_knowledge(
        self,
        query: str,
        study_id: str | None = None,
        document_ids: list[str] | None = None,
        limit: int = 10,
        similarity_threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        """Search knowledge base using vector similarity."""
        # Generate query embedding
        from app.services.llm_service import LLMService
        
        llm_service = LLMService(self.db)
        try:
            query_embedding = await llm_service.provider.embed(query)
        except Exception:
            return []

        # Build query for chunks
        chunk_query = select(KnowledgeChunk)
        
        if document_ids:
            chunk_query = chunk_query.where(
                KnowledgeChunk.document_id.in_(document_ids)
            )
        elif study_id:
            doc_query = select(Document.id).where(Document.study_id == study_id)
            chunk_query = chunk_query.where(
                KnowledgeChunk.document_id.in_(doc_query)
            )

        result = await self.db.execute(chunk_query)
        chunks = result.scalars().all()

        # Calculate similarity scores (cosine similarity)
        results = []
        for chunk in chunks:
            if not query_embedding:
                continue
                
            # For now, use simple relevance scoring
            # In production, use proper vector similarity with pgvector
            score = self._calculate_relevance(query, chunk.content)
            
            if score >= similarity_threshold:
                results.append({
                    "chunk": chunk,
                    "similarity_score": score,
                    "highlights": self._extract_highlights(query, chunk.content),
                })

        # Sort by score and limit
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:limit]

    def _calculate_relevance(self, query: str, content: str) -> float:
        """Calculate relevance score between query and content."""
        query_terms = set(query.lower().split())
        content_lower = content.lower()
        
        matches = sum(1 for term in query_terms if term in content_lower)
        
        if not query_terms:
            return 0.0
        
        return matches / len(query_terms)

    def _extract_highlights(self, query: str, content: str, window: int = 50) -> list[str]:
        """Extract highlighted snippets around matching terms."""
        highlights = []
        query_terms = query.lower().split()
        
        content_lower = content.lower()
        for term in query_terms:
            start = 0
            while True:
                pos = content_lower.find(term, start)
                if pos == -1:
                    break
                
                snippet_start = max(0, pos - window)
                snippet_end = min(len(content), pos + len(term) + window)
                snippet = content[snippet_start:snippet_end]
                
                highlights.append(f"...{snippet}...")
                start = pos + len(term)

        return list(set(highlights))[:3]  # Limit to 3 highlights

    async def get_chunk_with_document(self, chunk_id: str) -> dict[str, Any] | None:
        """Get a chunk with its parent document."""
        result = await self.db.execute(
            select(KnowledgeChunk).where(KnowledgeChunk.id == chunk_id)
        )
        chunk = result.scalar_one_or_none()
        if not chunk:
            return None

        doc_result = await self.db.execute(
            select(Document).where(Document.id == chunk.document_id)
        )
        document = doc_result.scalar_one_or_none()

        return {
            "chunk": chunk,
            "document": document,
        }

    async def create_citation(
        self,
        chunk_id: str,
        suggestion_id: str | None = None,
        relevance_score: float | None = None,
    ) -> Citation:
        """Create a citation linking a chunk to an LLM suggestion."""
        citation = Citation(
            chunk_id=chunk_id,
            suggestion_id=suggestion_id,
            relevance_score=relevance_score,
        )
        self.db.add(citation)
        await self.db.flush()
        await self.db.refresh(citation)
        return citation

    async def get_citations_for_suggestion(
        self,
        suggestion_id: str,
    ) -> list[dict[str, Any]]:
        """Get all citations for an LLM suggestion."""
        result = await self.db.execute(
            select(Citation).where(Citation.suggestion_id == suggestion_id)
        )
        citations = result.scalars().all()

        results = []
        for citation in citations:
            chunk_doc = await self.get_chunk_with_document(citation.chunk_id)
            if chunk_doc:
                results.append({
                    "citation": citation,
                    "chunk": chunk_doc["chunk"],
                    "document": chunk_doc["document"],
                })

        return results