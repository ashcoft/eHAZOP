"""Authentication service."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ehazop_backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from ehazop_backend.app.models.user import User
from ehazop_backend.app.schemas.user import UserCreate, UserResponse


class AuthService:
    """Authentication and user management service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate_user(self, email: str, password: str) -> User | None:
        """Authenticate a user by email and password."""
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        user = result.scalar_one_or_none()
        
        if user and verify_password(password, user.hashed_password):
            return user
        return None

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        user = User(
            email=user_data.email.lower(),
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            role=user_data.role,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Get a user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """Get a user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def update_last_login(self, user: User) -> None:
        """Update user's last login timestamp."""
        user.last_login = datetime.now(timezone.utc)
        await self.db.flush()

    def create_tokens(self, user: User) -> dict:
        """Create access and refresh tokens for a user."""
        token_data = {"sub": user.id, "email": user.email, "role": user.role}
        return {
            "access_token": create_access_token(token_data),
            "refresh_token": create_refresh_token(token_data),
            "token_type": "bearer",
        }

    async def update_user(
        self,
        user_id: str,
        email: str | None = None,
        full_name: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> User | None:
        """Update user fields."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        if email is not None:
            user.email = email.lower()
        if full_name is not None:
            user.full_name = full_name
        if role is not None:
            user.role = role
        if is_active is not None:
            user.is_active = is_active

        await self.db.flush()
        await self.db.refresh(user)
        return user