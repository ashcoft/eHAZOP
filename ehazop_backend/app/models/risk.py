"""Risk assessment models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RiskMatrix(Base):
    """Risk assessment matrix configuration."""

    __tablename__ = "risk_matrices"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    study_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )  # Optional: SAFAN, SYSOP, OPTAN, EHAZOP
    categories: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=["People", "Asset", "Environment", "Reputation"],
    )  # P/A/E/R
    severity_scale: Mapped[list[dict]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: [
            {"level": 1, "name": "Negligible", "description": "No injury, minimal impact"},
            {"level": 2, "name": "Minor", "description": "Minor injuries, limited damage"},
            {"level": 3, "name": "Moderate", "description": "Moderate injuries, significant damage"},
            {"level": 4, "name": "Major", "description": "Major injuries, extensive damage"},
            {"level": 5, "name": "Catastrophic", "description": "Fatalities, total loss"},
        ],
    )  # 1-5 scale
    likelihood_scale: Mapped[list[dict]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: [
            {"code": "A", "name": "Rare", "description": "May only occur in exceptional circumstances"},
            {"code": "B", "name": "Unlikely", "description": "Could occur but not expected"},
            {"code": "C", "name": "Possible", "description": "Might occur occasionally"},
            {"code": "D", "name": "Likely", "description": "Will probably occur"},
            {"code": "E", "name": "Almost Certain", "description": "Expected to occur frequently"},
        ],
    )  # A-E scale
    risk_bands: Mapped[list[dict]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: [
            {"name": "Low", "min_score": 0, "max_score": 5, "color": "green"},
            {"name": "Medium", "min_score": 6, "max_score": 10, "color": "yellow"},
            {"name": "High", "min_score": 11, "max_score": 15, "color": "orange"},
            {"name": "Very High", "min_score": 16, "max_score": 25, "color": "red"},
        ],
    )
    matrix_data: Mapped[list[list[int]]] = mapped_column(
        JSON,
        nullable=False,
    )  # 5x5 matrix of risk scores
    is_default: Mapped[bool] = mapped_column(
        default=False,
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
    studies: Mapped[list["Study"]] = relationship("Study")

    def __repr__(self) -> str:
        return f"<RiskMatrix {self.name}>"

    def calculate_risk_score(self, severity: int, likelihood: str) -> int:
        """Calculate risk score from severity (1-5) and likelihood (A-E)."""
        likelihood_index = ord(likelihood.upper()) - ord("A")
        if 0 <= likelihood_index < 5 and 1 <= severity <= 5:
            return self.matrix_data[severity - 1][likelihood_index]
        return 0

    def get_risk_band(self, score: int) -> str:
        """Get risk band for a given score."""
        for band in self.risk_bands:
            if band["min_score"] <= score <= band["max_score"]:
                return band["name"]
        return "Low"


class RiskMatrixOverride(Base):
    """Study-specific overrides for risk matrix cells."""

    __tablename__ = "risk_matrix_overrides"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    matrix_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("risk_matrices.id"),
        nullable=False,
    )
    study_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("studies.id"),
        nullable=True,
    )
    severity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )  # 1-5
    likelihood: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )  # A-E
    new_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    new_band: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow(),
    )