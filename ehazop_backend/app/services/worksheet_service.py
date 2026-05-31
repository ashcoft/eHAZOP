"""Deviation and worksheet management service."""

from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ehazop_backend.app.models.hazard import (
    Deviation,
    Cause,
    Consequence,
    Safeguard,
    RiskRanking,
    LLMSuggestion,
)
from ehazop_backend.app.models.action import Recommendation
from ehazop_backend.app.schemas.hazard import (
    DeviationCreate,
    DeviationUpdate,
    CauseCreate,
    ConsequenceCreate,
    SafeguardCreate,
    RiskRankingCreate,
)
from ehazop_backend.app.core.websocket import manager


class WorksheetService:
    """Service for managing deviations and worksheet data."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # Deviation operations
    async def create_deviation(self, deviation_data: DeviationCreate) -> Deviation:
        """Create a new deviation."""
        deviation = Deviation(
            node_id=deviation_data.node_id,
            guideword_id=deviation_data.guideword_id,
            reference=deviation_data.reference,
            deviation_text=deviation_data.deviation_text,
            location=deviation_data.location,
            consequence_summary=deviation_data.consequence_summary,
            status=deviation_data.status,
        )
        self.db.add(deviation)
        await self.db.flush()
        await self.db.refresh(deviation)
        return deviation

    async def get_deviation_by_id(self, deviation_id: str) -> Deviation | None:
        """Get a deviation by ID."""
        result = await self.db.execute(
            select(Deviation).where(Deviation.id == deviation_id)
        )
        return result.scalar_one_or_none()

    async def list_deviations(
        self,
        node_id: str | None = None,
        study_id: str | None = None,
        page: int = 1,
        page_size: int = 50,
        status: str | None = None,
    ) -> tuple[list[Deviation], int]:
        """List deviations with pagination."""
        query = select(Deviation)
        count_query = select(func.count(Deviation.id))

        if node_id:
            query = query.where(Deviation.node_id == node_id)
            count_query = count_query.where(Deviation.node_id == node_id)
        
        if study_id:
            from ehazop_backend.app.models.hazard import Node
            query = query.join(Node).where(Node.study_id == study_id)
            count_query = count_query.join(Node).where(Node.study_id == study_id)

        if status:
            query = query.where(Deviation.status == status)
            count_query = count_query.where(Deviation.status == status)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Deviation.reference)
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        deviations = list(result.scalars().all())

        return deviations, total

    async def update_deviation(
        self,
        deviation_id: str,
        deviation_data: DeviationUpdate,
        user_id: str | None = None,
        study_id: str | None = None,
    ) -> Deviation | None:
        """Update a deviation with optimistic concurrency."""
        deviation = await self.get_deviation_by_id(deviation_id)
        if not deviation:
            return None

        # Check version for optimistic concurrency
        if deviation_data.version is not None:
            if deviation.version != deviation_data.version:
                raise ValueError(
                    "Conflict: deviation was modified by another user. "
                    f"Expected version {deviation_data.version}, "
                    f"but current version is {deviation.version}"
                )

        update_data = deviation_data.model_dump(exclude_unset=True, exclude_none=True)
        for field, value in update_data.items():
            if field != "version":
                setattr(deviation, field, value)

        deviation.version += 1
        deviation.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(deviation)

        # Broadcast update via WebSocket
        if study_id:
            await manager.broadcast(
                study_id,
                {
                    "type": "deviation_update",
                    "deviation_id": deviation_id,
                    "version": deviation.version,
                    "user_id": user_id,
                },
            )

        return deviation

    async def delete_deviation(self, deviation_id: str) -> bool:
        """Delete a deviation."""
        deviation = await self.get_deviation_by_id(deviation_id)
        if not deviation:
            return False

        await self.db.delete(deviation)
        await self.db.flush()
        return True

    # Cause operations
    async def add_cause(self, cause_data: CauseCreate) -> Cause:
        """Add a cause to a deviation."""
        cause = Cause(
            deviation_id=cause_data.deviation_id,
            description=cause_data.description,
            likelihood=cause_data.likelihood,
        )
        self.db.add(cause)
        await self.db.flush()
        await self.db.refresh(cause)
        return cause

    async def get_causes(self, deviation_id: str) -> list[Cause]:
        """Get all causes for a deviation."""
        result = await self.db.execute(
            select(Cause).where(Cause.deviation_id == deviation_id)
        )
        return list(result.scalars().all())

    async def update_cause(self, cause_id: str, description: str | None = None, likelihood: str | None = None) -> Cause | None:
        """Update a cause."""
        result = await self.db.execute(select(Cause).where(Cause.id == cause_id))
        cause = result.scalar_one_or_none()
        if not cause:
            return None

        if description is not None:
            cause.description = description
        if likelihood is not None:
            cause.likelihood = likelihood
        await self.db.flush()
        await self.db.refresh(cause)
        return cause

    async def delete_cause(self, cause_id: str) -> bool:
        """Delete a cause."""
        result = await self.db.execute(select(Cause).where(Cause.id == cause_id))
        cause = result.scalar_one_or_none()
        if cause:
            await self.db.delete(cause)
            await self.db.flush()
            return True
        return False

    # Consequence operations
    async def add_consequence(self, consequence_data: ConsequenceCreate) -> Consequence:
        """Add a consequence to a deviation."""
        consequence = Consequence(
            deviation_id=consequence_data.deviation_id,
            description=consequence_data.description,
            category=consequence_data.category,
            severity=consequence_data.severity,
        )
        self.db.add(consequence)
        await self.db.flush()
        await self.db.refresh(consequence)
        return consequence

    async def get_consequences(self, deviation_id: str) -> list[Consequence]:
        """Get all consequences for a deviation."""
        result = await self.db.execute(
            select(Consequence).where(Consequence.deviation_id == deviation_id)
        )
        return list(result.scalars().all())

    async def update_consequence(
        self,
        consequence_id: str,
        description: str | None = None,
        category: str | None = None,
        severity: int | None = None,
    ) -> Consequence | None:
        """Update a consequence."""
        result = await self.db.execute(
            select(Consequence).where(Consequence.id == consequence_id)
        )
        consequence = result.scalar_one_or_none()
        if not consequence:
            return None

        if description is not None:
            consequence.description = description
        if category is not None:
            consequence.category = category
        if severity is not None:
            consequence.severity = severity
        await self.db.flush()
        await self.db.refresh(consequence)
        return consequence

    async def delete_consequence(self, consequence_id: str) -> bool:
        """Delete a consequence."""
        result = await self.db.execute(
            select(Consequence).where(Consequence.id == consequence_id)
        )
        consequence = result.scalar_one_or_none()
        if consequence:
            await self.db.delete(consequence)
            await self.db.flush()
            return True
        return False

    # Safeguard operations
    async def add_safeguard(self, safeguard_data: SafeguardCreate) -> Safeguard:
        """Add a safeguard to a deviation."""
        safeguard = Safeguard(
            deviation_id=safeguard_data.deviation_id,
            description=safeguard_data.description,
            safeguard_type=safeguard_data.safeguard_type,
        )
        self.db.add(safeguard)
        await self.db.flush()
        await self.db.refresh(safeguard)
        return safeguard

    async def get_safeguards(self, deviation_id: str) -> list[Safeguard]:
        """Get all safeguards for a deviation."""
        result = await self.db.execute(
            select(Safeguard).where(Safeguard.deviation_id == deviation_id)
        )
        return list(result.scalars().all())

    async def update_safeguard(
        self,
        safeguard_id: str,
        description: str | None = None,
        safeguard_type: str | None = None,
        is_active: bool | None = None,
    ) -> Safeguard | None:
        """Update a safeguard."""
        result = await self.db.execute(
            select(Safeguard).where(Safeguard.id == safeguard_id)
        )
        safeguard = result.scalar_one_or_none()
        if not safeguard:
            return None

        if description is not None:
            safeguard.description = description
        if safeguard_type is not None:
            safeguard.safeguard_type = safeguard_type
        if is_active is not None:
            safeguard.is_active = is_active
        await self.db.flush()
        await self.db.refresh(safeguard)
        return safeguard

    async def delete_safeguard(self, safeguard_id: str) -> bool:
        """Delete a safeguard."""
        result = await self.db.execute(
            select(Safeguard).where(Safeguard.id == safeguard_id)
        )
        safeguard = result.scalar_one_or_none()
        if safeguard:
            await self.db.delete(safeguard)
            await self.db.flush()
            return True
        return False

    # LLM Suggestion operations
    async def get_pending_suggestions(self, deviation_id: str) -> list[LLMSuggestion]:
        """Get pending LLM suggestions for a deviation."""
        result = await self.db.execute(
            select(LLMSuggestion).where(
                LLMSuggestion.deviation_id == deviation_id,
                LLMSuggestion.status == "pending",
            )
        )
        return list(result.scalars().all())

    async def accept_suggestion(
        self,
        suggestion_id: str,
        user_id: str,
    ) -> LLMSuggestion | None:
        """Accept an LLM suggestion and apply it to the deviation."""
        result = await self.db.execute(
            select(LLMSuggestion).where(LLMSuggestion.id == suggestion_id)
        )
        suggestion = result.scalar_one_or_none()
        if not suggestion:
            return None

        suggestion.status = "accepted"
        suggestion.reviewed_by_id = user_id
        suggestion.reviewed_at = datetime.now(timezone.utc)
        
        # Apply the suggestion to the deviation
        if suggestion.suggestion_type == "cause":
            cause = Cause(
                deviation_id=suggestion.deviation_id,
                description=suggestion.content,
            )
            self.db.add(cause)
        elif suggestion.suggestion_type == "consequence":
            consequence = Consequence(
                deviation_id=suggestion.deviation_id,
                description=suggestion.content,
            )
            self.db.add(consequence)
        elif suggestion.suggestion_type == "safeguard":
            safeguard = Safeguard(
                deviation_id=suggestion.deviation_id,
                description=suggestion.content,
            )
            self.db.add(safeguard)

        await self.db.flush()
        await self.db.refresh(suggestion)
        return suggestion

    async def reject_suggestion(
        self,
        suggestion_id: str,
        user_id: str,
    ) -> LLMSuggestion | None:
        """Reject an LLM suggestion."""
        result = await self.db.execute(
            select(LLMSuggestion).where(LLMSuggestion.id == suggestion_id)
        )
        suggestion = result.scalar_one_or_none()
        if not suggestion:
            return None

        suggestion.status = "rejected"
        suggestion.reviewed_by_id = user_id
        suggestion.reviewed_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(suggestion)
        return suggestion

    # Bulk operations
    async def apply_guidewords_to_node(
        self,
        node_id: str,
        guideword_ids: list[str],
        base_reference: str = "D",
    ) -> list[Deviation]:
        """Apply guidewords to create deviations for a node."""
        deviations = []
        for index, guideword_id in enumerate(guideword_ids):
            reference = f"{base_reference}-{len(deviations) + 1:03d}"
            deviation = Deviation(
                node_id=node_id,
                guideword_id=guideword_id,
                reference=reference,
            )
            self.db.add(deviation)
            deviations.append(deviation)

        await self.db.flush()
        for deviation in deviations:
            await self.db.refresh(deviation)
        return deviations