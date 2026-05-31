"""User model and related entities."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ehazop_backend.app.core.database import Base


class UserRole(str, Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    FACILITATOR = "facilitator"
    SCRIBE = "scribe"
    PARTICIPANT = "participant"
    VIEWER = "viewer"


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=UserRole.PARTICIPANT.value,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
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
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    memberships: Mapped[list["StudyMembership"]] = relationship(
        "StudyMembership",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    recommendations_owned: Mapped[list["Recommendation"]] = relationship(
        "Recommendation",
        back_populates="action_party_user",
        foreign_keys="Recommendation.action_party_id",
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class Study(Base):
    """SAFOP/EHAZOP study model."""

    __tablename__ = "studies"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    study_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # SAFAN, SYSOP, OPTAN, EHAZOP
    facility: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    scope: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
    )  # draft, in_progress, review, completed, archived
    revision: Mapped[int] = mapped_column(
        default=1,
        nullable=False,
    )
    confidentiality: Mapped[str] = mapped_column(
        String(50),
        default="internal",
    )  # public, internal, confidential, restricted
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    facilitator_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=True,
    )
    guideword_library_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("guideword_libraries.id"),
        nullable=True,
    )
    risk_matrix_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("risk_matrices.id"),
        nullable=True,
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
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    memberships: Mapped[list["StudyMembership"]] = relationship(
        "StudyMembership",
        back_populates="study",
        cascade="all, delete-orphan",
    )
    nodes: Mapped[list["Node"]] = relationship(
        "Node",
        back_populates="study",
        cascade="all, delete-orphan",
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="study",
        cascade="all, delete-orphan",
    )
    facilitator: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[facilitator_id],
    )
    created_by: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by_id],
    )
    guideword_library: Mapped["GuidewordLibrary | None"] = relationship(
        "GuidewordLibrary",
    )
    risk_matrix: Mapped["RiskMatrix | None"] = relationship(
        "RiskMatrix",
    )
    actions: Mapped[list["Recommendation"]] = relationship(
        "Recommendation",
        back_populates="study",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Study {self.name} ({self.study_type})>"


class StudyMembership(Base):
    """Study membership linking users to studies with roles."""

    __tablename__ = "study_memberships"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=False,
    )
    study_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("studies.id"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # facilitator, scribe, participant, viewer
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow(),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="memberships")
    study: Mapped["Study"] = relationship("Study", back_populates="memberships")

    def __repr__(self) -> str:
        return f"<StudyMembership {self.user_id} -> {self.study_id} ({self.role})>"


# Import AuditLog to avoid circular imports
from ehazop_backend.app.core.audit import AuditLog
from ehazop_backend.app.models.guideword import GuidewordLibrary
from ehazop_backend.app.models.risk import RiskMatrix
from ehazop_backend.app.models.action import Recommendation
from ehazop_backend.app.models.hazard import Node