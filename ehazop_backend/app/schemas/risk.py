"""Risk assessment schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RiskMatrixBase(BaseModel):
    """Base risk matrix schema."""
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    study_type: str | None = None
    categories: list[str] = ["People", "Asset", "Environment", "Reputation"]


class RiskMatrixCreate(RiskMatrixBase):
    """Risk matrix creation schema."""
    severity_scale: list[dict[str, Any]] | None = None
    likelihood_scale: list[dict[str, Any]] | None = None
    risk_bands: list[dict[str, Any]] | None = None
    matrix_data: list[list[int]] | None = None
    is_default: bool = False


class RiskMatrixUpdate(BaseModel):
    """Risk matrix update schema."""
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    study_type: str | None = None
    severity_scale: list[dict[str, Any]] | None = None
    likelihood_scale: list[dict[str, Any]] | None = None
    risk_bands: list[dict[str, Any]] | None = None
    matrix_data: list[list[int]] | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class RiskMatrixResponse(BaseModel):
    """Risk matrix response schema."""
    id: str
    name: str
    description: str | None = None
    study_type: str | None = None
    categories: list[str]
    severity_scale: list[dict[str, Any]]
    likelihood_scale: list[dict[str, Any]]
    risk_bands: list[dict[str, Any]]
    matrix_data: list[list[int]]
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RiskMatrixListResponse(BaseModel):
    """Paginated risk matrix list response."""
    items: list[RiskMatrixResponse]
    total: int
    page: int
    page_size: int


class RiskMatrixOverrideBase(BaseModel):
    """Base risk matrix override schema."""
    severity: int = Field(ge=1, le=5)
    likelihood: str = Field(pattern="^[A-E]$")
    new_score: int = Field(ge=0)
    new_band: str | None = None
    reason: str | None = None


class RiskMatrixOverrideCreate(RiskMatrixOverrideBase):
    """Risk matrix override creation schema."""
    matrix_id: str
    study_id: str | None = None


class RiskMatrixOverrideResponse(BaseModel):
    """Risk matrix override response schema."""
    id: str
    matrix_id: str
    study_id: str | None
    severity: int
    likelihood: str
    new_score: int
    new_band: str | None = None
    reason: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RiskScoreRequest(BaseModel):
    """Request to calculate risk score."""
    severity: int = Field(ge=1, le=5)
    likelihood: str = Field(pattern="^[A-E]$")
    matrix_id: str | None = None  # Use default if not provided


class RiskScoreResponse(BaseModel):
    """Risk score calculation response."""
    severity: int
    likelihood: str
    risk_score: int
    risk_band: str
    category: str
    matrix_name: str | None = None