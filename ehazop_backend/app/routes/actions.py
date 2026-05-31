"""Report generation routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.action import (
    RecommendationCreate,
    RecommendationUpdate,
    RecommendationResponse,
    RecommendationListResponse,
    RecommendationHistoryResponse,
    RecommendationVerify,
)
from app.services.action_service import ActionService

router = APIRouter(prefix="/actions", tags=["Actions"])


@router.get("", response_model=RecommendationListResponse)
async def list_recommendations(
    study_id: str | None = None,
    deviation_id: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    assigned_to: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List recommendations with filters."""
    action_service = ActionService(db)
    recommendations, total = await action_service.list_recommendations(
        study_id=study_id,
        deviation_id=deviation_id,
        status=status,
        priority=priority,
        assigned_to=assigned_to,
        page=page,
        page_size=page_size,
    )

    return RecommendationListResponse(
        items=[RecommendationResponse.model_validate(r) for r in recommendations],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=RecommendationResponse, status_code=status.HTTP_201_CREATED)
async def create_recommendation(
    recommendation_data: RecommendationCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new recommendation."""
    action_service = ActionService(db)
    recommendation = await action_service.create_recommendation(
        recommendation_data, current_user.id
    )
    return RecommendationResponse.model_validate(recommendation)


@router.get("/{recommendation_id}", response_model=RecommendationResponse)
async def get_recommendation(
    recommendation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a recommendation by ID."""
    action_service = ActionService(db)
    recommendation = await action_service.get_recommendation_by_id(recommendation_id)
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found",
        )
    return RecommendationResponse.model_validate(recommendation)


@router.patch("/{recommendation_id}", response_model=RecommendationResponse)
async def update_recommendation(
    recommendation_id: str,
    recommendation_data: RecommendationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a recommendation."""
    action_service = ActionService(db)
    recommendation = await action_service.update_recommendation(
        recommendation_id, recommendation_data, current_user.id
    )
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found",
        )
    return RecommendationResponse.model_validate(recommendation)


@router.post("/{recommendation_id}/verify", response_model=RecommendationResponse)
async def verify_recommendation(
    recommendation_id: str,
    verification_data: RecommendationVerify,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Verify a completed recommendation."""
    action_service = ActionService(db)
    recommendation = await action_service.verify_recommendation(
        recommendation_id,
        verification_data.verification_evidence,
        verification_data.verification_date,
        current_user.id,
    )
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found",
        )
    return RecommendationResponse.model_validate(recommendation)


@router.post("/{recommendation_id}/carry-forward", response_model=RecommendationResponse)
async def carry_forward_recommendation(
    recommendation_id: str,
    target_study_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Carry forward a recommendation to another study."""
    action_service = ActionService(db)
    recommendation = await action_service.carry_forward_recommendation(
        recommendation_id, target_study_id, current_user.id
    )
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found",
        )
    return RecommendationResponse.model_validate(recommendation)


@router.get("/{recommendation_id}/history", response_model=list[RecommendationHistoryResponse])
async def get_recommendation_history(
    recommendation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get history of changes to a recommendation."""
    action_service = ActionService(db)
    history = await action_service.get_recommendation_history(recommendation_id)
    return [RecommendationHistoryResponse.model_validate(h) for h in history]


@router.get("/overdue", response_model=RecommendationListResponse)
async def get_overdue_actions(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get all overdue actions."""
    action_service = ActionService(db)
    recommendations = await action_service.get_overdue_actions()
    
    return RecommendationListResponse(
        items=[RecommendationResponse.model_validate(r) for r in recommendations],
        total=len(recommendations),
        page=1,
        page_size=len(recommendations),
    )


@router.get("/study/{study_id}/summary")
async def get_action_summary(
    study_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get summary of actions for a study."""
    action_service = ActionService(db)
    summary = await action_service.get_action_summary(study_id)
    return summary