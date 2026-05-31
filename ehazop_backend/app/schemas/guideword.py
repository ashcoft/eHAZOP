"""Guideword library schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class GuidewordLibraryBase(BaseModel):
    """Base guideword library schema."""
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    study_type: Literal["SAFAN", "SYSOP", "OPTAN", "EHAZOP", "generic"] = "generic"
    category: str | None = Field(default=None, max_length=100)


class GuidewordLibraryCreate(GuidewordLibraryBase):
    """Guideword library creation schema."""
    is_default: bool = False


class GuidewordLibraryUpdate(BaseModel):
    """Guideword library update schema."""
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    category: str | None = Field(default=None, max_length=100)
    is_default: bool | None = None
    is_active: bool | None = None


class GuidewordLibraryResponse(BaseModel):
    """Guideword library response schema."""
    id: str
    name: str
    description: str | None = None
    study_type: str
    category: str | None = None
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    guideword_count: int | None = None

    model_config = {"from_attributes": True}


class GuidewordBase(BaseModel):
    """Base guideword schema."""
    code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    deviation_template: str | None = None
    order_index: int = 0


class GuidewordCreate(GuidewordBase):
    """Guideword creation schema."""
    library_id: str


class GuidewordUpdate(BaseModel):
    """Guideword update schema."""
    code: str | None = Field(default=None, min_length=1, max_length=20)
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    deviation_template: str | None = None
    order_index: int | None = None
    is_active: bool | None = None


class GuidewordResponse(BaseModel):
    """Guideword response schema."""
    id: str
    library_id: str
    code: str
    name: str
    description: str | None = None
    deviation_template: str | None = None
    order_index: int
    is_active: bool

    model_config = {"from_attributes": True}