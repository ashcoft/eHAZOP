"""Action and recommendation tracking service."""

from datetime import date, datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ehazop_backend.app.models.action import Recommendation, RecommendationHistory
from ehazop_backend.app.schemas.action import RecommendationCreate, RecommendationUpdate


class ActionService:
    """Service for managing recommendations and action tracking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_recommendation(
        self,
        recommendation_data: RecommendationCreate,
        created_by_id: str,
    ) -> Recommendation:
        """Create a new recommendation."""
        # Get next reference number
        reference = await self._generate_reference(recommendation_data.study_id)

        recommendation = Recommendation(
            deviation_id=recommendation_data.deviation_id,
            study_id=recommendation_data.study_id,
            reference=reference,
            description=recommendation_data.description,
            priority=recommendation_data.priority,
            target_date=recommendation_data.target_date,
            action_party_id=recommendation_data.action_party_id,
            created_by_id=created_by_id,
        )
        self.db.add(recommendation)
        await self.db.flush()
        await self.db.refresh(recommendation)
        return recommendation

    async def _generate_reference(self, study_id: str) -> str:
        """Generate next recommendation reference."""
        result = await self.db.execute(
            select(func.count(Recommendation.id)).where(
                Recommendation.study_id == study_id
            )
        )
        count = result.scalar() or 0
        return f"ACT-{count + 1:03d}"

    async def get_recommendation_by_id(self, recommendation_id: str) -> Recommendation | None:
        """Get a recommendation by ID."""
        result = await self.db.execute(
            select(Recommendation).where(Recommendation.id == recommendation_id)
        )
        return result.scalar_one_or_none()

    async def list_recommendations(
        self,
        study_id: str | None = None,
        deviation_id: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        assigned_to: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Recommendation], int]:
        """List recommendations with filters."""
        query = select(Recommendation)
        count_query = select(func.count(Recommendation.id))

        if study_id:
            query = query.where(Recommendation.study_id == study_id)
            count_query = count_query.where(Recommendation.study_id == study_id)
        if deviation_id:
            query = query.where(Recommendation.deviation_id == deviation_id)
            count_query = count_query.where(Recommendation.deviation_id == deviation_id)
        if status:
            query = query.where(Recommendation.status == status)
            count_query = count_query.where(Recommendation.status == status)
        if priority:
            query = query.where(Recommendation.priority == priority)
            count_query = count_query.where(Recommendation.priority == priority)
        if assigned_to:
            query = query.where(Recommendation.action_party_id == assigned_to)
            count_query = count_query.where(Recommendation.action_party_id == assigned_to)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Recommendation.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        recommendations = list(result.scalars().all())

        return recommendations, total

    async def update_recommendation(
        self,
        recommendation_id: str,
        recommendation_data: RecommendationUpdate,
        user_id: str,
    ) -> Recommendation | None:
        """Update a recommendation."""
        recommendation = await self.get_recommendation_by_id(recommendation_id)
        if not recommendation:
            return None

        # Track changes for history
        update_data = recommendation_data.model_dump(exclude_unset=True)
        for field, new_value in update_data.items():
            old_value = getattr(recommendation, field)
            if old_value != new_value:
                # Create history entry
                history = RecommendationHistory(
                    recommendation_id=recommendation_id,
                    changed_by_id=user_id,
                    field_name=field,
                    old_value=str(old_value) if old_value is not None else None,
                    new_value=str(new_value) if new_value is not None else None,
                )
                self.db.add(history)
                setattr(recommendation, field, new_value)

        recommendation.updated_at = datetime.now(timezone.utc)
        
        # Set completed date if status changed to completed
        if recommendation_data.status == "completed" and recommendation.completed_date is None:
            recommendation.completed_date = date.today()

        await self.db.flush()
        await self.db.refresh(recommendation)
        return recommendation

    async def verify_recommendation(
        self,
        recommendation_id: str,
        verification_evidence: str,
        verification_date: date | None,
        verified_by_id: str,
    ) -> Recommendation | None:
        """Verify a completed recommendation."""
        recommendation = await self.get_recommendation_by_id(recommendation_id)
        if not recommendation:
            return None

        recommendation.status = "verified"
        recommendation.verification_evidence = verification_evidence
        recommendation.verification_date = verification_date or date.today()
        recommendation.verification_by_id = verified_by_id
        recommendation.updated_at = datetime.now(timezone.utc)

        # Create history entry
        history = RecommendationHistory(
            recommendation_id=recommendation_id,
            changed_by_id=verified_by_id,
            field_name="status",
            old_value=recommendation.status,
            new_value="verified",
            change_reason=f"Verified: {verification_evidence}",
        )
        self.db.add(history)

        await self.db.flush()
        await self.db.refresh(recommendation)
        return recommendation

    async def carry_forward_recommendation(
        self,
        recommendation_id: str,
        target_study_id: str,
        user_id: str,
    ) -> Recommendation | None:
        """Carry forward a recommendation to another study."""
        original = await self.get_recommendation_by_id(recommendation_id)
        if not original:
            return None

        # Link to original
        linked = await self.create_recommendation(
            RecommendationCreate(
                deviation_id=None,
                study_id=target_study_id,
                description=original.description,
                priority=original.priority,
                target_date=None,
            ),
            created_by_id=user_id,
        )

        # Mark original as carried forward
        original.status = "carried_forward"
        original.linked_recommendation_id = linked.id
        original.updated_at = datetime.now(timezone.utc)

        # Create history entries
        history_original = RecommendationHistory(
            recommendation_id=recommendation_id,
            changed_by_id=user_id,
            field_name="status",
            old_value=original.status,
            new_value="carried_forward",
            change_reason=f"Carried forward to {linked.reference}",
        )
        self.db.add(history_original)

        await self.db.flush()
        await self.db.refresh(original)
        return original

    async def get_recommendation_history(
        self,
        recommendation_id: str,
    ) -> list[RecommendationHistory]:
        """Get history of changes to a recommendation."""
        result = await self.db.execute(
            select(RecommendationHistory)
            .where(RecommendationHistory.recommendation_id == recommendation_id)
            .order_by(RecommendationHistory.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_overdue_actions(self, days_overdue: int = 0) -> list[Recommendation]:
        """Get actions that are overdue."""
        today = date.today()
        query = select(Recommendation).where(
            Recommendation.status.in_(["open", "in_progress"]),
            Recommendation.target_date < today,
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_action_summary(self, study_id: str) -> dict:
        """Get summary of actions for a study."""
        recommendations, _ = await self.list_recommendations(study_id=study_id)
        
        summary = {
            "total": len(recommendations),
            "open": sum(1 for r in recommendations if r.status == "open"),
            "in_progress": sum(1 for r in recommendations if r.status == "in_progress"),
            "completed": sum(1 for r in recommendations if r.status == "completed"),
            "verified": sum(1 for r in recommendations if r.status == "verified"),
            "carried_forward": sum(1 for r in recommendations if r.status == "carried_forward"),
            "overdue": sum(
                1 for r in recommendations 
                if r.status in ["open", "in_progress"] and r.target_date and r.target_date < date.today()
            ),
            "by_priority": {
                "critical": sum(1 for r in recommendations if r.priority == "critical"),
                "high": sum(1 for r in recommendations if r.priority == "high"),
                "medium": sum(1 for r in recommendations if r.priority == "medium"),
                "low": sum(1 for r in recommendations if r.priority == "low"),
            },
        }
        
        return summary