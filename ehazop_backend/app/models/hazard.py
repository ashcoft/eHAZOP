"""Hazard and Node models for HAZOP studies."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Node(Base):
    """HAZOP study node (equipment, system, or sub-system)."""

    __tablename__ = "nodes"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    study_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("studies.id"),
        nullable=False,
    )
    reference: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # e.g., "N-001", "GEN-01"
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    design_intent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    equipment_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )  # e.g., "Generator", "Switchboard", "Transformer"
    drawing_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    node_category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )  # For EHAZOP: power_generation, distribution, protection, etc.
    operational_mode: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )  # e.g., "normal", "startup", "shutdown", "maintenance"
    order_index: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
    )

    # Relationships
    study: Mapped["Study"] = relationship("Study", back_populates="nodes")
    deviations: Mapped[list["Deviation"]] = relationship(
        "Deviation",
        back_populates="node",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Node {self.reference}: {self.name}>"


class Deviation(Base):
    """Deviation record from applying guidewords to a node."""

    __tablename__ = "deviations"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    node_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("nodes.id"),
        nullable=False,
    )
    guideword_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("guidewords.id"),
        nullable=False,
    )
    reference: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # e.g., "D-001"
    deviation_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    consequence_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="open",
        nullable=False,
    )  # open, in_progress, closed, carried_forward
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
    )

    # Relationships
    node: Mapped["Node"] = relationship("Node", back_populates="deviations")
    guideword: Mapped["Guideword"] = relationship("Guideword")
    causes: Mapped[list["Cause"]] = relationship(
        "Cause",
        back_populates="deviation",
        cascade="all, delete-orphan",
    )
    consequences: Mapped[list["Consequence"]] = relationship(
        "Consequence",
        back_populates="deviation",
        cascade="all, delete-orphan",
    )
    safeguards: Mapped[list["Safeguard"]] = relationship(
        "Safeguard",
        back_populates="deviation",
        cascade="all, delete-orphan",
    )
    risk_rankings: Mapped[list["RiskRanking"]] = relationship(
        "RiskRanking",
        back_populates="deviation",
        cascade="all, delete-orphan",
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        "Recommendation",
        back_populates="deviation",
        cascade="all, delete-orphan",
    )
    llm_suggestions: Mapped[list["LLMSuggestion"]] = relationship(
        "LLMSuggestion",
        back_populates="deviation",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Deviation {self.reference}>"


class Cause(Base):
    """Cause of a deviation."""

    __tablename__ = "causes"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    deviation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("deviations.id"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    likelihood: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )  # A-E scale
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow(),
    )

    # Relationships
    deviation: Mapped["Deviation"] = relationship("Deviation", back_populates="causes")


class Consequence(Base):
    """Consequence of a deviation."""

    __tablename__ = "consequences"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    deviation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("deviations.id"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )  # People, Asset, Environment, Reputation
    severity: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )  # 1-5 scale
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow(),
    )

    # Relationships
    deviation: Mapped["Deviation"] = relationship("Deviation", back_populates="consequences")


class Safeguard(Base):
    """Existing safeguard for a deviation."""

    __tablename__ = "safeguards"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    deviation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("deviations.id"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    safeguard_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )  # preventive, detective, mitigative
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow(),
    )

    # Relationships
    deviation: Mapped["Deviation"] = relationship("Deviation", back_populates="safeguards")


class LLMSuggestion(Base):
    """AI-generated suggestion pending human review."""

    __tablename__ = "llm_suggestions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    deviation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("deviations.id"),
        nullable=False,
    )
    suggestion_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # cause, consequence, safeguard
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    citations: Mapped[list[dict] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    confidence: Mapped[float | None] = mapped_column(
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
    )  # pending, accepted, rejected
    reviewed_by_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow(),
    )

    # Relationships
    deviation: Mapped["Deviation"] = relationship("Deviation", back_populates="llm_suggestions")
    reviewed_by: Mapped["User | None"] = relationship("User")


# Import Study for relationship
from app.models.user import Study
from app.models.guideword import Guideword


class RiskRanking(Base):
    """Risk ranking for a deviation consequence."""

    __tablename__ = "risk_rankings"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    deviation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("deviations.id"),
        nullable=False,
    )
    consequence_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("consequences.id"),
        nullable=True,
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # People, Asset, Environment, Reputation
    severity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )  # 1-5
    likelihood: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )  # A-E
    risk_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    risk_band: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )  # Low, Medium, High, Very High
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
    )

    # Relationships
    deviation: Mapped["Deviation"] = relationship("Deviation", back_populates="risk_rankings")
    consequence: Mapped["Consequence | None"] = relationship("Consequence")