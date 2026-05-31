"""Study management service."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ehazop_backend.app.models.user import Study, StudyMembership, User
from ehazop_backend.app.models.action import Recommendation
from ehazop_backend.app.schemas.user import StudyCreate, StudyUpdate
from ehazop_backend.app.core.audit import create_audit_entry


class StudyService:
    """Service for managing studies."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_study(
        self,
        study_data: StudyCreate,
        created_by_id: str,
    ) -> Study:
        """Create a new study."""
        study = Study(
            name=study_data.name,
            study_type=study_data.study_type,
            facility=study_data.facility,
            scope=study_data.scope,
            confidentiality=study_data.confidentiality,
            description=study_data.description,
            guideword_library_id=study_data.guideword_library_id,
            risk_matrix_id=study_data.risk_matrix_id,
            created_by_id=created_by_id,
            facilitator_id=created_by_id,
        )
        self.db.add(study)
        await self.db.flush()

        # Add creator as facilitator
        membership = StudyMembership(
            user_id=created_by_id,
            study_id=study.id,
            role="facilitator",
        )
        self.db.add(membership)

        # Add additional members
        for member_id in study_data.member_ids:
            member = StudyMembership(
                user_id=member_id,
                study_id=study.id,
                role="participant",
            )
            self.db.add(member)

        await self.db.flush()
        await self.db.refresh(study)
        return study

    async def get_study_by_id(self, study_id: str) -> Study | None:
        """Get a study by ID."""
        result = await self.db.execute(select(Study).where(Study.id == study_id))
        return result.scalar_one_or_none()

    async def list_studies(
        self,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        study_type: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Study], int]:
        """List studies with pagination and filters."""
        query = select(Study)
        count_query = select(func.count(Study.id))

        if status:
            query = query.where(Study.status == status)
            count_query = count_query.where(Study.status == status)
        if study_type:
            query = query.where(Study.study_type == study_type)
            count_query = count_query.where(Study.study_type == study_type)
        if search:
            query = query.where(Study.name.ilike(f"%{search}%"))
            count_query = count_query.where(Study.name.ilike(f"%{search}%"))

        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = query.order_by(Study.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        studies = list(result.scalars().all())

        return studies, total

    async def update_study(
        self,
        study_id: str,
        study_data: StudyUpdate,
        user_id: str,
    ) -> Study | None:
        """Update a study."""
        study = await self.get_study_by_id(study_id)
        if not study:
            return None

        update_data = study_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(study, field, value)

        study.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(study)
        return study

    async def delete_study(self, study_id: str) -> bool:
        """Delete a study (soft delete by archiving)."""
        study = await self.get_study_by_id(study_id)
        if not study:
            return False

        study.status = "archived"
        study.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True

    async def add_member(
        self,
        study_id: str,
        user_id: str,
        role: str,
    ) -> StudyMembership:
        """Add a member to a study."""
        membership = StudyMembership(
            user_id=user_id,
            study_id=study_id,
            role=role,
        )
        self.db.add(membership)
        await self.db.flush()
        return membership

    async def remove_member(self, study_id: str, user_id: str) -> bool:
        """Remove a member from a study."""
        result = await self.db.execute(
            select(StudyMembership).where(
                StudyMembership.study_id == study_id,
                StudyMembership.user_id == user_id,
            )
        )
        membership = result.scalar_one_or_none()
        if membership:
            await self.db.delete(membership)
            await self.db.flush()
            return True
        return False

    async def get_members(self, study_id: str) -> list[StudyMembership]:
        """Get all members of a study."""
        result = await self.db.execute(
            select(StudyMembership).where(StudyMembership.study_id == study_id)
        )
        return list(result.scalars().all())

    async def start_study(self, study_id: str) -> Study | None:
        """Mark a study as in progress."""
        study = await self.get_study_by_id(study_id)
        if not study:
            return None

        study.status = "in_progress"
        study.started_at = datetime.now(timezone.utc)
        study.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(study)
        return study

    async def complete_study(self, study_id: str) -> Study | None:
        """Mark a study as completed."""
        study = await self.get_study_by_id(study_id)
        if not study:
            return None

        study.status = "completed"
        study.completed_at = datetime.now(timezone.utc)
        study.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(study)
        return study

    async def get_study_stats(self, study_id: str) -> dict[str, Any]:
        """Get statistics for a study."""
        study = await self.get_study_by_id(study_id)
        if not study:
            return {}

        # Count nodes
        from ehazop_backend.app.models.hazard import Node
        nodes_result = await self.db.execute(
            select(func.count(Node.id)).where(Node.study_id == study_id)
        )
        node_count = nodes_result.scalar() or 0

        # Count deviations
        from ehazop_backend.app.models.hazard import Deviation
        deviations_result = await self.db.execute(
            select(func.count(Deviation.id))
            .join(Node)
            .where(Node.study_id == study_id)
        )
        deviation_count = deviations_result.scalar() or 0

        # Count open actions
        actions_result = await self.db.execute(
            select(func.count(Recommendation.id))
            .where(
                Recommendation.study_id == study_id,
                Recommendation.status.in_(["open", "in_progress"]),
            )
        )
        open_actions = actions_result.scalar() or 0

        return {
            "node_count": node_count,
            "deviation_count": deviation_count,
            "open_actions": open_actions,
            "status": study.status,
            "revision": study.revision,
        }