"""User and authentication schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


# Auth schemas
class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


# User schemas
class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    role: Literal["admin", "facilitator", "scribe", "participant", "viewer"] = "participant"


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    """User update schema."""
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    role: Literal["admin", "facilitator", "scribe", "participant", "viewer"] | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    """User response schema."""
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None = None

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """Paginated user list response."""
    items: list[UserResponse]
    total: int
    page: int
    page_size: int


# Study membership schemas
class StudyMembershipBase(BaseModel):
    """Base membership schema."""
    study_id: str
    role: Literal["facilitator", "scribe", "participant", "viewer"]


class StudyMembershipCreate(StudyMembershipBase):
    """Membership creation schema."""
    user_id: str


class StudyMembershipResponse(BaseModel):
    """Membership response schema."""
    id: str
    user_id: str
    study_id: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


# Study schemas
class StudyBase(BaseModel):
    """Base study schema."""
    name: str = Field(min_length=1, max_length=255)
    study_type: Literal["SAFAN", "SYSOP", "OPTAN", "EHAZOP"]
    facility: str = Field(min_length=1, max_length=255)
    scope: str | None = None
    confidentiality: Literal["public", "internal", "confidential", "restricted"] = "internal"


class StudyCreate(StudyBase):
    """Study creation schema."""
    description: str | None = None
    guideword_library_id: str | None = None
    risk_matrix_id: str | None = None
    member_ids: list[str] = []


class StudyUpdate(BaseModel):
    """Study update schema."""
    name: str | None = Field(default=None, min_length=1, max_length=255)
    study_type: Literal["SAFAN", "SYSOP", "OPTAN", "EHAZOP"] | None = None
    facility: str | None = Field(default=None, min_length=1, max_length=255)
    scope: str | None = None
    status: Literal["draft", "in_progress", "review", "completed", "archived"] | None = None
    confidentiality: Literal["public", "internal", "confidential", "restricted"] | None = None
    description: str | None = None
    guideword_library_id: str | None = None
    risk_matrix_id: str | None = None


class StudyResponse(BaseModel):
    """Study response schema."""
    id: str
    name: str
    study_type: str
    facility: str
    scope: str | None = None
    status: str
    revision: int
    confidentiality: str
    description: str | None = None
    facilitator_id: str | None = None
    guideword_library_id: str | None = None
    risk_matrix_id: str | None = None
    created_by_id: str
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    member_count: int | None = None
    node_count: int | None = None
    action_count: int | None = None

    model_config = {"from_attributes": True}


class StudyListResponse(BaseModel):
    """Paginated study list response."""
    items: list[StudyResponse]
    total: int
    page: int
    page_size: int


class StudyMemberAdd(BaseModel):
    """Schema to add a member to a study."""
    user_id: str
    role: Literal["facilitator", "scribe", "participant", "viewer"]