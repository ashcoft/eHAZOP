"""FastAPI dependencies for authentication and authorization."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ehazop_backend.app.core.database import get_db
from ehazop_backend.app.core.security import verify_access_token
from ehazop_backend.app.models.user import User, StudyMembership

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Get the current authenticated user from JWT token."""
    try:
        payload = verify_access_token(credentials.credentials)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


class RequireRoles:
    """Dependency to require specific roles."""

    def __init__(self, *roles: str):
        self.roles = set(roles)

    async def __call__(self, user: CurrentUser) -> User:
        if user.role not in self.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of the following roles: {', '.join(self.roles)}",
            )
        return user


# Pre-configured role dependencies
require_admin = RequireRoles("admin")
require_facilitator = RequireRoles("admin", "facilitator")
require_scribe = RequireRoles("admin", "facilitator", "scribe")
require_participant = RequireRoles("admin", "facilitator", "scribe", "participant")
require_viewer = RequireRoles("admin", "facilitator", "scribe", "participant", "viewer")


async def get_study_membership(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    study_id: str | None = None,
) -> StudyMembership | None:
    """Get study membership for current user and optional study."""
    if study_id is None:
        return None
    
    from ehazop_backend.app.models.user import StudyMembership
    result = await db.execute(
        select(StudyMembership).where(
            StudyMembership.user_id == user.id,
            StudyMembership.study_id == study_id,
        )
    )
    return result.scalar_one_or_none()


async def require_study_access(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    study_id: str,
    require_role: str | None = None,
) -> StudyMembership:
    """Require the user to have access to a specific study."""
    membership = await get_study_membership(user, db, study_id)
    
    if membership is None:
        # Check if user is admin (admins have global access)
        if user.role == "admin":
            return None
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this study",
        )
    
    if require_role:
        role_hierarchy = {"viewer": 1, "participant": 2, "scribe": 3, "facilitator": 4, "admin": 5}
        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(require_role, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {require_role} role or higher",
            )
    
    return membership


StudyAccess = Annotated[StudyMembership, Depends(get_study_membership)]