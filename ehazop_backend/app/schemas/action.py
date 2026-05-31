"""Action and recommendation schemas."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class RecommendationBase(BaseModel):
    """Base recommendation schema."""
    description: str = Field(min_length=1)
    priority: Literal["low", "medium", "high", "critical"] = "medium"


class RecommendationCreate(RecommendationBase):
    """Recommendation creation schema."""
    deviation_id: str | None = None
    study_id: str
    target_date: date | None = None
    action_party_id: str | None = None


class RecommendationUpdate(BaseModel):
    """Recommendation update schema."""
    description: str | None = Field(default=None, min_length=1)
    priority: Literal["low", "medium", "high", "critical"] | None = None
    status: Literal["open", "in_progress", "completed", "verified", "carried_forward", "closed"] | None = None
    action_party_id: str | None = None
    target_date: date | None = None
    completed_date: date | None = None
    verification_date: date | None = None
    verification_evidence: str | None = None
    notes: str | None = None


class RecommendationResponse(BaseModel):
    """Recommendation response schema."""
    id: str
    deviation_id: str | None
    study_id: str
    reference: str
    description: str
    priority: str
    status: str
    action_party_id: str | None
    target_date: date | None
    completed_date: date | None
    verification_date: date | None
    verification_evidence: str | None
    linked_recommendation_id: str | None
    notes: str | None
    order_index: int
    created_by_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RecommendationListResponse(BaseModel):
    """Paginated recommendation list response."""
    items: list[RecommendationResponse]
    total: int
    page: int
    page_size: int


class RecommendationHistoryResponse(BaseModel):
    """Recommendation history response schema."""
    id: str
    recommendation_id: str
    changed_by_id: str
    field_name: str
    old_value: str | None
    new_value: str | None
    change_reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RecommendationVerify(BaseModel):
    """Schema for verifying/completing a recommendation."""
    verification_evidence: str = Field(min_length=1)
    verification_date: date | None = None