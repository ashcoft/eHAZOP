"""Hazard and node schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# Node schemas
class NodeBase(BaseModel):
    """Base node schema."""
    reference: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    design_intent: str | None = None
    equipment_type: str | None = Field(default=None, max_length=100)
    drawing_reference: str | None = Field(default=None, max_length=255)
    node_category: str | None = Field(default=None, max_length=100)
    operational_mode: str | None = Field(default=None, max_length=100)


class NodeCreate(NodeBase):
    """Node creation schema."""
    study_id: str
    order_index: int = 0


class NodeUpdate(BaseModel):
    """Node update schema."""
    reference: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    design_intent: str | None = None
    equipment_type: str | None = Field(default=None, max_length=100)
    drawing_reference: str | None = Field(default=None, max_length=255)
    node_category: str | None = Field(default=None, max_length=100)
    operational_mode: str | None = Field(default=None, max_length=100)
    order_index: int | None = None
    is_active: bool | None = None


class NodeResponse(BaseModel):
    """Node response schema."""
    id: str
    study_id: str
    reference: str
    name: str
    description: str | None = None
    design_intent: str | None = None
    equipment_type: str | None = None
    drawing_reference: str | None = None
    node_category: str | None = None
    operational_mode: str | None = None
    order_index: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deviation_count: int | None = None

    model_config = {"from_attributes": True}


class NodeListResponse(BaseModel):
    """Paginated node list response."""
    items: list[NodeResponse]
    total: int
    page: int
    page_size: int


# Deviation schemas
class DeviationBase(BaseModel):
    """Base deviation schema."""
    guideword_id: str
    reference: str = Field(min_length=1, max_length=50)
    deviation_text: str | None = None
    location: str | None = None
    consequence_summary: str | None = None
    status: Literal["open", "in_progress", "closed", "carried_forward"] = "open"


class DeviationCreate(DeviationBase):
    """Deviation creation schema."""
    node_id: str


class DeviationUpdate(BaseModel):
    """Deviation update schema."""
    deviation_text: str | None = None
    location: str | None = None
    consequence_summary: str | None = None
    status: Literal["open", "in_progress", "closed", "carried_forward"] | None = None
    version: int | None = None  # For optimistic concurrency


class DeviationResponse(BaseModel):
    """Deviation response schema."""
    id: str
    node_id: str
    guideword_id: str
    reference: str
    deviation_text: str | None = None
    location: str | None = None
    consequence_summary: str | None = None
    status: str
    version: int
    created_at: datetime
    updated_at: datetime
    cause_count: int | None = None
    consequence_count: int | None = None
    safeguard_count: int | None = None
    recommendation_count: int | None = None

    model_config = {"from_attributes": True}


class DeviationDetailResponse(DeviationResponse):
    """Detailed deviation with all related data."""
    causes: list["CauseResponse"] = []
    consequences: list["ConsequenceResponse"] = []
    safeguards: list["SafeguardResponse"] = []
    recommendations: list["RecommendationResponse"] = []
    risk_rankings: list["RiskRankingResponse"] = []
    guideword: "GuidewordResponse" | None = None


# Cause schemas
class CauseBase(BaseModel):
    """Base cause schema."""
    description: str = Field(min_length=1)
    likelihood: Literal["A", "B", "C", "D", "E"] | None = None


class CauseCreate(CauseBase):
    """Cause creation schema."""
    deviation_id: str


class CauseResponse(BaseModel):
    """Cause response schema."""
    id: str
    deviation_id: str
    description: str
    likelihood: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# Consequence schemas
class ConsequenceBase(BaseModel):
    """Base consequence schema."""
    description: str = Field(min_length=1)
    category: Literal["People", "Asset", "Environment", "Reputation"] | None = None
    severity: int | None = Field(default=None, ge=1, le=5)


class ConsequenceCreate(ConsequenceBase):
    """Consequence creation schema."""
    deviation_id: str


class ConsequenceResponse(BaseModel):
    """Consequence response schema."""
    id: str
    deviation_id: str
    description: str
    category: str | None = None
    severity: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# Safeguard schemas
class SafeguardBase(BaseModel):
    """Base safeguard schema."""
    description: str = Field(min_length=1)
    safeguard_type: Literal["preventive", "detective", "mitigative"] | None = None


class SafeguardCreate(SafeguardBase):
    """Safeguard creation schema."""
    deviation_id: str


class SafeguardResponse(BaseModel):
    """Safeguard response schema."""
    id: str
    deviation_id: str
    description: str
    safeguard_type: str | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# Risk ranking schemas
class RiskRankingBase(BaseModel):
    """Base risk ranking schema."""
    category: Literal["People", "Asset", "Environment", "Reputation"]
    severity: int = Field(ge=1, le=5)
    likelihood: Literal["A", "B", "C", "D", "E"]


class RiskRankingCreate(RiskRankingBase):
    """Risk ranking creation schema."""
    deviation_id: str
    consequence_id: str | None = None


class RiskRankingResponse(BaseModel):
    """Risk ranking response schema."""
    id: str
    deviation_id: str
    consequence_id: str | None = None
    category: str
    severity: int
    likelihood: str
    risk_score: int
    risk_band: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# LLM Suggestion schemas
class LLMSuggestionBase(BaseModel):
    """Base LLM suggestion schema."""
    suggestion_type: Literal["cause", "consequence", "safeguard"]
    content: str = Field(min_length=1)


class LLMSuggestionCreate(LLMSuggestionBase):
    """LLM suggestion creation schema."""
    deviation_id: str


class LLMSuggestionResponse(BaseModel):
    """LLM suggestion response schema."""
    id: str
    deviation_id: str
    suggestion_type: str
    content: str
    citations: list[dict] | None = None
    confidence: float | None = None
    status: str
    reviewed_by_id: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LLMSuggestionReview(BaseModel):
    """Schema for reviewing LLM suggestions."""
    accept: bool
    action: Literal["accept", "reject"]


# Guideword schemas
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


# Recommendation schemas (for worksheet view)
class RecommendationResponse(BaseModel):
    """Recommendation response schema."""
    id: str
    deviation_id: str | None
    study_id: str
    reference: str
    description: str
    priority: str
    status: str
    action_party_id: str | None = None
    target_date: datetime | None = None
    completed_date: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# Update forward references
DeviationDetailResponse.model_rebuild()