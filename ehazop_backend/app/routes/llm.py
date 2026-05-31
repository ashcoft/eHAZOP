"""LLM service routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.services.llm_service import LLMService
from app.schemas.hazard import LLMSuggestionResponse

router = APIRouter(prefix="/llm", tags=["LLM"])


@router.post("/suggest/{deviation_id}")
async def generate_suggestions(
    deviation_id: str,
    suggestion_type: str,  # cause, consequence, safeguard
    context: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate LLM suggestions for a deviation."""
    llm_service = LLMService(db)
    try:
        suggestions = await llm_service.generate_and_store_suggestions(
            deviation_id, suggestion_type, context
        )
        return {
            "suggestions": [LLMSuggestionResponse.model_validate(s) for s in suggestions],
            "count": len(suggestions),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM generation failed: {str(e)}",
        )


@router.post("/suggest-with-context/{deviation_id}")
async def generate_suggestions_with_context(
    deviation_id: str,
    suggestion_type: str,
    context: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate LLM suggestions with additional context."""
    llm_service = LLMService(db)
    try:
        suggestions = await llm_service.generate_and_store_suggestions(
            deviation_id, suggestion_type, context
        )
        return {
            "suggestions": [LLMSuggestionResponse.model_validate(s) for s in suggestions],
            "count": len(suggestions),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM generation failed: {str(e)}",
        )