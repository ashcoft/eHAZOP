"""Study management routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.user import (
    StudyCreate,
    StudyUpdate,
    StudyResponse,
    StudyListResponse,
    StudyMemberAdd,
)
from app.services.study_service import StudyService

router = APIRouter(prefix="/studies", tags=["Studies"])


@router.get("", response_model=StudyListResponse)
async def list_studies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    study_type: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List studies the user has access to."""
    study_service = StudyService(db)
    studies, total = await study_service.list_studies(
        page=page,
        page_size=page_size,
        status=status,
        study_type=study_type,
        search=search,
    )

    # Convert to response format
    study_responses = []
    for study in studies:
        # Get member count
        from app.models.user import StudyMembership
        from sqlalchemy import select, func
        count_result = await db.execute(
            select(func.count(StudyMembership.id)).where(
                StudyMembership.study_id == study.id
            )
        )
        member_count = count_result.scalar() or 0

        study_resp = StudyResponse(
            id=study.id,
            name=study.name,
            study_type=study.study_type,
            facility=study.facility,
            scope=study.scope,
            status=study.status,
            revision=study.revision,
            confidentiality=study.confidentiality,
            description=study.description,
            facilitator_id=study.facilitator_id,
            guideword_library_id=study.guideword_library_id,
            risk_matrix_id=study.risk_matrix_id,
            created_by_id=study.created_by_id,
            created_at=study.created_at,
            updated_at=study.updated_at,
            started_at=study.started_at,
            completed_at=study.completed_at,
            member_count=member_count,
        )
        study_responses.append(study_resp)

    return StudyListResponse(
        items=study_responses,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=StudyResponse, status_code=status.HTTP_201_CREATED)
async def create_study(
    study_data: StudyCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new study."""
    study_service = StudyService(db)
    study = await study_service.create_study(study_data, current_user.id)
    return StudyResponse.model_validate(study)


@router.get("/{study_id}", response_model=StudyResponse)
async def get_study(
    study_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get study by ID."""
    study_service = StudyService(db)
    study = await study_service.get_study_by_id(study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found",
        )

    # Check access
    from app.models.user import StudyMembership
    from sqlalchemy import select, func
    membership_result = await db.execute(
        select(StudyMembership).where(
            StudyMembership.study_id == study_id,
            StudyMembership.user_id == current_user.id,
        )
    )
    membership = membership_result.scalar_one_or_none()
    
    # Admins have global access
    if not membership and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this study",
        )

    # Get member count
    count_result = await db.execute(
        select(func.count(StudyMembership.id)).where(
            StudyMembership.study_id == study_id
        )
    )
    member_count = count_result.scalar() or 0

    return StudyResponse(
        id=study.id,
        name=study.name,
        study_type=study.study_type,
        facility=study.facility,
        scope=study.scope,
        status=study.status,
        revision=study.revision,
        confidentiality=study.confidentiality,
        description=study.description,
        facilitator_id=study.facilitator_id,
        guideword_library_id=study.guideword_library_id,
        risk_matrix_id=study.risk_matrix_id,
        created_by_id=study.created_by_id,
        created_at=study.created_at,
        updated_at=study.updated_at,
        started_at=study.started_at,
        completed_at=study.completed_at,
        member_count=member_count,
    )


@router.patch("/{study_id}", response_model=StudyResponse)
async def update_study(
    study_id: str,
    study_data: StudyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a study."""
    study_service = StudyService(db)
    study = await study_service.update_study(study_id, study_data, current_user.id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found",
        )

    return StudyResponse.model_validate(study)


@router.post("/{study_id}/start", response_model=StudyResponse)
async def start_study(
    study_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Mark a study as in progress."""
    study_service = StudyService(db)
    study = await study_service.start_study(study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found",
        )

    return StudyResponse.model_validate(study)


@router.post("/{study_id}/complete", response_model=StudyResponse)
async def complete_study(
    study_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Mark a study as completed."""
    study_service = StudyService(db)
    study = await study_service.complete_study(study_id)
    if not study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found",
        )

    return StudyResponse.model_validate(study)


@router.delete("/{study_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_study(
    study_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Archive a study (soft delete)."""
    if current_user.role not in ["admin", "facilitator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only facilitators and admins can delete studies",
        )

    study_service = StudyService(db)
    success = await study_service.delete_study(study_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study not found",
        )


@router.post("/{study_id}/members", status_code=status.HTTP_201_CREATED)
async def add_member(
    study_id: str,
    member_data: StudyMemberAdd,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Add a member to a study."""
    if current_user.role not in ["admin", "facilitator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only facilitators and admins can add members",
        )

    study_service = StudyService(db)
    membership = await study_service.add_member(
        study_id, member_data.user_id, member_data.role
    )

    return {"id": membership.id, "user_id": membership.user_id, "role": membership.role}


@router.delete("/{study_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    study_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Remove a member from a study."""
    if current_user.role not in ["admin", "facilitator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only facilitators and admins can remove members",
        )

    study_service = StudyService(db)
    success = await study_service.remove_member(study_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found",
        )