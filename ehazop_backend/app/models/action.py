"""Action and recommendation tracking models."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Recommendation(Base):
    """Recommendation/action from a deviation."""

    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    deviation_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("deviations.id"),
        nullable=True,
    )
    study_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("studies.id"),
        nullable=False,
    )
    reference: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # e.g., "ACT-001"
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    priority: Mapped[str] = mapped_column(
        String(20),
        default="medium",
        nullable=False,
    )  # low, medium, high, critical
    status: Mapped[str] = mapped_column(
        String(50),
        default="open",
        nullable=False,
    )  # open, in_progress, completed, verified, carried_forward, closed
    action_party_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=True,
    )
    target_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    completed_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    verification_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    verification_evidence: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    verification_by_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=True,
    )
    linked_recommendation_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("recommendations.id"),
        nullable=True,
    )  # For carry-forward between studies
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    created_by_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
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
    deviation: Mapped["Deviation | None"] = relationship(
        "Deviation",
        back_populates="recommendations",
    )
    study: Mapped["Study"] = relationship("Study", back_populates="actions")
    action_party_user: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[action_party_id],
        back_populates="recommendations_owned",
    )
    created_by: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by_id],
    )
    verification_by: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[verification_by_id],
    )
    linked_recommendation: Mapped["Recommendation | None"] = relationship(
        "Recommendation",
        remote_side=[id],
    )
    history: Mapped[list["RecommendationHistory"]] = relationship(
        "RecommendationHistory",
        back_populates="recommendation",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Recommendation {self.reference}>"


class RecommendationHistory(Base):
    """History of changes to recommendations for audit trail."""

    __tablename__ = "recommendation_history"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    recommendation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("recommendations.id"),
        nullable=False,
    )
    changed_by_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=False,
    )
    field_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    old_value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    new_value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    change_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow(),
    )

    # Relationships
    recommendation: Mapped["Recommendation"] = relationship(
        "Recommendation",
        back_populates="history",
    )
    changed_by: Mapped["User"] = relationship("User")


# Import Deviation for relationship
from app.models.hazard import Deviation
from app.models.user import Study, User