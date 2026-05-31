"""Knowledge base and RAG routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from ehazop_backend.app.core.database import get_db
from ehazop_backend.app.core.dependencies import get_current_user
from ehazop_backend.app.schemas.knowledge import (
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSearchResult,
    DocumentIngestRequest,
    DocumentResponse,
    DocumentListResponse,
)
from ehazop_backend.app.services.rag_service import RAGService
from ehazop_backend.app.services.storage_service import StorageService

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    search_request: KnowledgeSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Search the knowledge base for relevant content."""
    rag_service = RAGService(db)
    results = await rag_service.search_knowledge(
        query=search_request.query,
        study_id=search_request.study_id,
        document_ids=search_request.document_ids,
        limit=search_request.limit,
        similarity_threshold=search_request.similarity_threshold,
    )

    search_results = []
    for result in results:
        from ehazop_backend.app.schemas.knowledge import KnowledgeChunkResponse
        from ehazop_backend.app.schemas.hazard import NodeResponse
        
        search_results.append(KnowledgeSearchResult(
            chunk=KnowledgeChunkResponse.model_validate(result["chunk"]),
            document=result.get("document") if result.get("document") else None,
            similarity_score=result["similarity_score"],
            highlights=result["highlights"],
        ))

    return KnowledgeSearchResponse(
        results=search_results,
        total=len(search_results),
        query=search_request.query,
    )


@router.post("/ingest/{document_id}")
async def ingest_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Ingest a document into the knowledge base."""
    rag_service = RAGService(db)
    try:
        chunks = await rag_service.ingest_document(document_id)
        
        # Generate embeddings
        await rag_service.generate_embeddings(chunks)
        
        return {
            "status": "success",
            "chunks_created": len(chunks),
            "document_id": document_id,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}",
        )


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    study_id: str | None = None,
    document_type: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List documents in the knowledge base."""
    storage_service = StorageService(db)
    documents, total = await storage_service.list_documents(
        study_id=study_id,
        document_type=document_type,
        page=page,
        page_size=page_size,
    )

    return DocumentListResponse(
        items=[DocumentResponse.model_validate(d) for d in documents],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/documents/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    study_id: str | None = None,
    document_type: str = "other",
    description: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Upload a document to the knowledge base."""
    content = await file.read()
    
    storage_service = StorageService(db)
    result = await storage_service.upload_file(
        content=content,
        filename=file.filename,
        file_type=file.content_type or "application/octet-stream",
        study_id=study_id,
        document_type=document_type,
        mime_type=file.content_type or "application/octet-stream",
        uploaded_by_id=current_user.id,
    )

    from ehazop_backend.app.schemas.knowledge import DocumentResponse
    return result