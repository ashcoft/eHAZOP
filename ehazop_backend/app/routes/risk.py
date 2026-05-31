"""Risk matrix routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.risk import (
    RiskMatrixCreate,
    RiskMatrixUpdate,
    RiskMatrixResponse,
    RiskMatrixListResponse,
    RiskScoreRequest,
    RiskScoreResponse,
)
from app.services.risk_service import RiskService

router = APIRouter(prefix="/risk-matrices", tags=["Risk Matrices"])


@router.get("", response_model=RiskMatrixListResponse)
async def list_matrices(
    study_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all risk matrices."""
    risk_service = RiskService(db)
    matrices = await risk_service.list_matrices(study_type=study_type)
    return RiskMatrixListResponse(
        items=[RiskMatrixResponse.model_validate(m) for m in matrices],
        total=len(matrices),
        page=1,
        page_size=len(matrices),
    )


@router.post("", response_model=RiskMatrixResponse, status_code=status.HTTP_201_CREATED)
async def create_matrix(
    matrix_data: RiskMatrixCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new risk matrix."""
    if current_user.role not in ["admin", "facilitator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only facilitators and admins can create risk matrices",
        )

    risk_service = RiskService(db)
    matrix = await risk_service.create_matrix(matrix_data)
    return RiskMatrixResponse.model_validate(matrix)


@router.get("/{matrix_id}", response_model=RiskMatrixResponse)
async def get_matrix(
    matrix_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a risk matrix by ID."""
    risk_service = RiskService(db)
    matrix = await risk_service.get_matrix_by_id(matrix_id)
    if not matrix:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk matrix not found",
        )
    return RiskMatrixResponse.model_validate(matrix)


@router.patch("/{matrix_id}", response_model=RiskMatrixResponse)
async def update_matrix(
    matrix_id: str,
    matrix_data: RiskMatrixUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a risk matrix."""
    if current_user.role not in ["admin", "facilitator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only facilitators and admins can update risk matrices",
        )

    risk_service = RiskService(db)
    matrix = await risk_service.update_matrix(matrix_id, matrix_data)
    if not matrix:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk matrix not found",
        )
    return RiskMatrixResponse.model_validate(matrix)


@router.delete("/{matrix_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_matrix(
    matrix_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a risk matrix (soft delete)."""
    if current_user.role not in ["admin", "facilitator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only facilitators and admins can delete risk matrices",
        )

    risk_service = RiskService(db)
    success = await risk_service.delete_matrix(matrix_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk matrix not found",
        )


@router.get("/calculate", response_model=RiskScoreResponse)
async def calculate_risk_score(
    severity: int = Query(..., ge=1, le=5),
    likelihood: str = Query(..., pattern="^[A-E]$"),
    matrix_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Calculate risk score from severity and likelihood."""
    risk_service = RiskService(db)
    score, band, matrix_name = await risk_service.calculate_risk_score(
        severity, likelihood, matrix_id
    )
    return RiskScoreResponse(
        severity=severity,
        likelihood=likelihood,
        risk_score=score,
        risk_band=band,
        category="",
        matrix_name=matrix_name,
    )


@router.get("/default", response_model=RiskMatrixResponse)
async def get_default_matrix(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get the default risk matrix."""
    risk_service = RiskService(db)
    matrix = await risk_service.get_default_matrix()
    if not matrix:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No default risk matrix found",
        )
    return RiskMatrixResponse.model_validate(matrix)