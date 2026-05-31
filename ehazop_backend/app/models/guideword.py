"""Guideword library models for SAFOP/EHAZOP."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ehazop_backend.app.core.database import Base


class GuidewordLibrary(Base):
    """Library of guidewords for a specific study type."""

    __tablename__ = "guideword_libraries"

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
    study_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # SAFAN, SYSOP, OPTAN, EHAZOP, or generic
    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )  # fault, operating, system/discrimination, operational-mode
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
    guidewords: Mapped[list["Guideword"]] = relationship(
        "Guideword",
        back_populates="library",
        cascade="all, delete-orphan",
    )
    studies: Mapped[list["Study"]] = relationship("Study")

    def __repr__(self) -> str:
        return f"<GuidewordLibrary {self.name} ({self.study_type})>"


class Guideword(Base):
    """Individual guideword in a library."""

    __tablename__ = "guidewords"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    library_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("guideword_libraries.id"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # e.g., "NO", "MORE", "LESS", "AS_WELL_AS"
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )  # e.g., "None/Nothing", "More", "Less"
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    deviation_template: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )  # Template for deviation text, e.g., "No {parameter}"
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

    # Relationships
    library: Mapped["GuidewordLibrary"] = relationship(
        "GuidewordLibrary",
        back_populates="guidewords",
    )
    deviations: Mapped[list["Deviation"]] = relationship("Deviation")

    def __repr__(self) -> str:
        return f"<Guideword {self.code}: {self.name}>"