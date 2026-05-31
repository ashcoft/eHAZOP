"""Deviation and worksheet routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ehazop_backend.app.core.database import get_db
from ehazop_backend.app.core.dependencies import get_current_user
from ehazop_backend.app.schemas.hazard import (
    DeviationCreate,
    DeviationUpdate,
    DeviationResponse,
    DeviationDetailResponse,
    CauseCreate,
    CauseResponse,
    ConsequenceCreate,
    ConsequenceResponse,
    SafeguardCreate,
    SafeguardResponse,
    RiskRankingCreate,
    RiskRankingResponse,
    LLMSuggestionResponse,
    LLMSuggestionReview,
)
from ehazop_backend.app.services.worksheet_service import WorksheetService

router = APIRouter(tags=["Worksheet"])


@router.get("/nodes/{node_id}/deviations", response_model=list[DeviationResponse])
async def list_deviations(
    node_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all deviations for a node."""
    worksheet_service = WorksheetService(db)
    deviations, _ = await worksheet_service.list_deviations(
        node_id=node_id,
        page=page,
        page_size=page_size,
        status=status,
    )
    return [DeviationResponse.model_validate(d) for d in deviations]


@router.post("/nodes/{node_id}/deviations", response_model=DeviationResponse, status_code=status.HTTP_201_CREATED)
async def create_deviation(
    node_id: str,
    deviation_data: DeviationCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new deviation."""
    if deviation_data.node_id != node_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Node ID mismatch",
        )

    worksheet_service = WorksheetService(db)
    deviation = await worksheet_service.create_deviation(deviation_data)
    return DeviationResponse.model_validate(deviation)


@router.get("/deviations/{deviation_id}", response_model=DeviationResponse)
async def get_deviation(
    deviation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a deviation by ID."""
    worksheet_service = WorksheetService(db)
    deviation = await worksheet_service.get_deviation_by_id(deviation_id)
    if not deviation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deviation not found",
        )
    return DeviationResponse.model_validate(deviation)


@router.patch("/deviations/{deviation_id}", response_model=DeviationResponse)
async def update_deviation(
    deviation_id: str,
    deviation_data: DeviationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a deviation."""
    worksheet_service = WorksheetService(db)
    try:
        deviation = await worksheet_service.update_deviation(
            deviation_id, deviation_data, current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    if not deviation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deviation not found",
        )
    return DeviationResponse.model_validate(deviation)


@router.delete("/deviations/{deviation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deviation(
    deviation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a deviation."""
    worksheet_service = WorksheetService(db)
    success = await worksheet_service.delete_deviation(deviation_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deviation not found",
        )


# Cause routes
@router.post("/deviations/{deviation_id}/causes", response_model=CauseResponse, status_code=status.HTTP_201_CREATED)
async def add_cause(
    deviation_id: str,
    cause_data: CauseCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Add a cause to a deviation."""
    if cause_data.deviation_id != deviation_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deviation ID mismatch",
        )

    worksheet_service = WorksheetService(db)
    cause = await worksheet_service.add_cause(cause_data)
    return CauseResponse.model_validate(cause)


@router.get("/deviations/{deviation_id}/causes", response_model=list[CauseResponse])
async def list_causes(
    deviation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all causes for a deviation."""
    worksheet_service = WorksheetService(db)
    causes = await worksheet_service.get_causes(deviation_id)
    return [CauseResponse.model_validate(c) for c in causes]


# Consequence routes
@router.post("/deviations/{deviation_id}/consequences", response_model=ConsequenceResponse, status_code=status.HTTP_201_CREATED)
async def add_consequence(
    deviation_id: str,
    consequence_data: ConsequenceCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Add a consequence to a deviation."""
    if consequence_data.deviation_id != deviation_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deviation ID mismatch",
        )

    worksheet_service = WorksheetService(db)
    consequence = await worksheet_service.add_consequence(consequence_data)
    return ConsequenceResponse.model_validate(consequence)


@router.get("/deviations/{deviation_id}/consequences", response_model=list[ConsequenceResponse])
async def list_consequences(
    deviation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all consequences for a deviation."""
    worksheet_service = WorksheetService(db)
    consequences = await worksheet_service.get_consequences(deviation_id)
    return [ConsequenceResponse.model_validate(c) for c in consequences]


# Safeguard routes
@router.post("/deviations/{deviation_id}/safeguards", response_model=SafeguardResponse, status_code=status.HTTP_201_CREATED)
async def add_safeguard(
    deviation_id: str,
    safeguard_data: SafeguardCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Add a safeguard to a deviation."""
    if safeguard_data.deviation_id != deviation_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deviation ID mismatch",
        )

    worksheet_service = WorksheetService(db)
    safeguard = await worksheet_service.add_safeguard(safeguard_data)
    return SafeguardResponse.model_validate(safeguard)


@router.get("/deviations/{deviation_id}/safeguards", response_model=list[SafeguardResponse])
async def list_safeguards(
    deviation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all safeguards for a deviation."""
    worksheet_service = WorksheetService(db)
    safeguards = await worksheet_service.get_safeguards(deviation_id)
    return [SafeguardResponse.model_validate(s) for s in safeguards]


# Risk ranking routes
@router.post("/deviations/{deviation_id}/risk-rankings", response_model=RiskRankingResponse, status_code=status.HTTP_201_CREATED)
async def add_risk_ranking(
    deviation_id: str,
    ranking_data: RiskRankingCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Add a risk ranking to a deviation."""
    from ehazop_backend.app.services.risk_service import RiskService
    risk_service = RiskService(db)
    ranking = await risk_service.create_risk_ranking(
        deviation_id=deviation_id,
        category=ranking_data.category,
        severity=ranking_data.severity,
        likelihood=ranking_data.likelihood,
        consequence_id=ranking_data.consequence_id,
    )
    return RiskRankingResponse.model_validate(ranking)


# LLM suggestion routes
@router.get("/deviations/{deviation_id}/suggestions", response_model=list[LLMSuggestionResponse])
async def get_pending_suggestions(
    deviation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get pending LLM suggestions for a deviation."""
    worksheet_service = WorksheetService(db)
    suggestions = await worksheet_service.get_pending_suggestions(deviation_id)
    return [LLMSuggestionResponse.model_validate(s) for s in suggestions]


@router.post("/deviations/{deviation_id}/suggestions/{suggestion_id}/accept", response_model=LLMSuggestionResponse)
async def accept_suggestion(
    deviation_id: str,
    suggestion_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Accept an LLM suggestion."""
    worksheet_service = WorksheetService(db)
    suggestion = await worksheet_service.accept_suggestion(suggestion_id, current_user.id)
    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suggestion not found",
        )
    return LLMSuggestionResponse.model_validate(suggestion)


@router.post("/deviations/{deviation_id}/suggestions/{suggestion_id}/reject", response_model=LLMSuggestionResponse)
async def reject_suggestion(
    deviation_id: str,
    suggestion_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Reject an LLM suggestion."""
    worksheet_service = WorksheetService(db)
    suggestion = await worksheet_service.reject_suggestion(suggestion_id, current_user.id)
    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suggestion not found",
        )
    return LLMSuggestionResponse.model_validate(suggestion)