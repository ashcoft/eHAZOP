"""Guideword library routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.guideword import (
    GuidewordLibraryCreate,
    GuidewordLibraryUpdate,
    GuidewordLibraryResponse,
    GuidewordCreate,
    GuidewordUpdate,
    GuidewordResponse,
)

router = APIRouter(prefix="/guideword-libraries", tags=["Guideword Libraries"])


@router.get("", response_model=list[GuidewordLibraryResponse])
async def list_libraries(
    study_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all guideword libraries."""
    from sqlalchemy import select
    from app.models.guideword import GuidewordLibrary

    query = select(GuidewordLibrary).where(GuidewordLibrary.is_active == True)
    if study_type:
        query = query.where(GuidewordLibrary.study_type == study_type)

    result = await db.execute(query.order_by(GuidewordLibrary.name))
    libraries = result.scalars().all()

    responses = []
    for lib in libraries:
        from sqlalchemy import func
        count_result = await db.execute(
            select(func.count()).select_from(GuidewordLibrary).where(
                GuidewordLibrary.id == lib.id
            )
        )
        gw_count = len(lib.guidewords) if lib.guidewords else 0
        
        responses.append(GuidewordLibraryResponse(
            id=lib.id,
            name=lib.name,
            description=lib.description,
            study_type=lib.study_type,
            category=lib.category,
            is_default=lib.is_default,
            is_active=lib.is_active,
            created_at=lib.created_at,
            updated_at=lib.updated_at,
            guideword_count=gw_count,
        ))

    return responses


@router.post("", response_model=GuidewordLibraryResponse, status_code=status.HTTP_201_CREATED)
async def create_library(
    library_data: GuidewordLibraryCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new guideword library."""
    if current_user.role not in ["admin", "facilitator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only facilitators and admins can create guideword libraries",
        )

    from app.models.guideword import GuidewordLibrary
    
    library = GuidewordLibrary(
        name=library_data.name,
        description=library_data.description,
        study_type=library_data.study_type,
        category=library_data.category,
        is_default=library_data.is_default,
    )
    db.add(library)
    await db.flush()
    await db.refresh(library)

    return GuidewordLibraryResponse.model_validate(library)


@router.get("/{library_id}", response_model=GuidewordLibraryResponse)
async def get_library(
    library_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a guideword library by ID."""
    from sqlalchemy import select
    from app.models.guideword import GuidewordLibrary

    result = await db.execute(select(GuidewordLibrary).where(GuidewordLibrary.id == library_id))
    library = result.scalar_one_or_none()
    if not library:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guideword library not found",
        )

    return GuidewordLibraryResponse.model_validate(library)


@router.patch("/{library_id}", response_model=GuidewordLibraryResponse)
async def update_library(
    library_id: str,
    library_data: GuidewordLibraryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a guideword library."""
    if current_user.role not in ["admin", "facilitator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only facilitators and admins can update guideword libraries",
        )

    from sqlalchemy import select
    from app.models.guideword import GuidewordLibrary

    result = await db.execute(select(GuidewordLibrary).where(GuidewordLibrary.id == library_id))
    library = result.scalar_one_or_none()
    if not library:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guideword library not found",
        )

    update_data = library_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(library, field, value)

    await db.flush()
    await db.refresh(library)

    return GuidewordLibraryResponse.model_validate(library)


# Guideword routes
@router.get("/{library_id}/guidewords", response_model=list[GuidewordResponse])
async def list_guidewords(
    library_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all guidewords in a library."""
    from sqlalchemy import select
    from app.models.guideword import Guideword

    result = await db.execute(
        select(Guideword)
        .where(Guideword.library_id == library_id, Guideword.is_active == True)
        .order_by(Guideword.order_index)
    )
    guidewords = result.scalars().all()

    return [GuidewordResponse.model_validate(gw) for gw in guidewords]


@router.post("/{library_id}/guidewords", response_model=GuidewordResponse, status_code=status.HTTP_201_CREATED)
async def create_guideword(
    library_id: str,
    guideword_data: GuidewordCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new guideword in a library."""
    if guideword_data.library_id != library_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Library ID mismatch",
        )

    if current_user.role not in ["admin", "facilitator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only facilitators and admins can create guidewords",
        )

    from app.models.guideword import Guideword
    
    guideword = Guideword(
        library_id=library_id,
        code=guideword_data.code,
        name=guideword_data.name,
        description=guideword_data.description,
        deviation_template=guideword_data.deviation_template,
        order_index=guideword_data.order_index,
    )
    db.add(guideword)
    await db.flush()
    await db.refresh(guideword)

    return GuidewordResponse.model_validate(guideword)