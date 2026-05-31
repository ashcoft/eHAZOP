"""Risk assessment service."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.risk import RiskMatrix, RiskMatrixOverride
from app.models.hazard import RiskRanking, Consequence
from app.schemas.risk import RiskMatrixCreate, RiskMatrixUpdate


class RiskService:
    """Service for risk assessment and matrix management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # Risk Matrix operations
    async def create_matrix(self, matrix_data: RiskMatrixCreate) -> RiskMatrix:
        """Create a new risk matrix."""
        # Set default matrix data if not provided
        if matrix_data.matrix_data is None:
            matrix_data.matrix_data = self._generate_default_matrix()

        matrix = RiskMatrix(
            name=matrix_data.name,
            description=matrix_data.description,
            study_type=matrix_data.study_type,
            categories=matrix_data.categories,
            severity_scale=matrix_data.severity_scale,
            likelihood_scale=matrix_data.likelihood_scale,
            risk_bands=matrix_data.risk_bands,
            matrix_data=matrix_data.matrix_data,
            is_default=matrix_data.is_default,
        )
        self.db.add(matrix)
        await self.db.flush()

        # If this is default, unset other defaults
        if matrix.is_default:
            await self._unset_default_matrices(matrix.id)

        await self.db.refresh(matrix)
        return matrix

    def _generate_default_matrix(self) -> list[list[int]]:
        """Generate a default 5x5 risk matrix."""
        return [
            [1, 2, 3, 4, 5],   # Severity 1
            [2, 4, 6, 8, 10],  # Severity 2
            [3, 6, 9, 12, 15], # Severity 3
            [4, 8, 12, 16, 20],# Severity 4
            [5, 10, 15, 20, 25],# Severity 5
        ]

    async def _unset_default_matrices(self, exclude_id: str) -> None:
        """Unset default flag on all other matrices."""
        result = await self.db.execute(
            select(RiskMatrix).where(
                RiskMatrix.id != exclude_id,
                RiskMatrix.is_default == True,
            )
        )
        for matrix in result.scalars().all():
            matrix.is_default = False
        await self.db.flush()

    async def get_matrix_by_id(self, matrix_id: str) -> RiskMatrix | None:
        """Get a risk matrix by ID."""
        result = await self.db.execute(
            select(RiskMatrix).where(RiskMatrix.id == matrix_id)
        )
        return result.scalar_one_or_none()

    async def get_default_matrix(self) -> RiskMatrix | None:
        """Get the default risk matrix."""
        result = await self.db.execute(
            select(RiskMatrix).where(RiskMatrix.is_default == True)
        )
        return result.scalar_one_or_none()

    async def list_matrices(
        self,
        study_type: str | None = None,
        is_active: bool = True,
    ) -> list[RiskMatrix]:
        """List risk matrices with optional filtering."""
        query = select(RiskMatrix)
        
        if study_type:
            query = query.where(RiskMatrix.study_type == study_type)
        if is_active is not None:
            query = query.where(RiskMatrix.is_active == is_active)

        query = query.order_by(RiskMatrix.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_matrix(
        self,
        matrix_id: str,
        matrix_data: RiskMatrixUpdate,
    ) -> RiskMatrix | None:
        """Update a risk matrix."""
        matrix = await self.get_matrix_by_id(matrix_id)
        if not matrix:
            return None

        update_data = matrix_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(matrix, field, value)

        matrix.updated_at = datetime.now(timezone.utc)

        # If setting as default, unset others
        if matrix.is_default:
            await self._unset_default_matrices(matrix.id)

        await self.db.flush()
        await self.db.refresh(matrix)
        return matrix

    async def delete_matrix(self, matrix_id: str) -> bool:
        """Delete a risk matrix (soft delete)."""
        matrix = await self.get_matrix_by_id(matrix_id)
        if not matrix:
            return False

        matrix.is_active = False
        matrix.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True

    # Risk Ranking operations
    async def calculate_risk_score(
        self,
        severity: int,
        likelihood: str,
        matrix_id: str | None = None,
    ) -> tuple[int, str, str | None]:
        """Calculate risk score and band from severity and likelihood."""
        matrix = await self.get_matrix_by_id(matrix_id) if matrix_id else None
        if not matrix:
            matrix = await self.get_default_matrix()
        
        if not matrix:
            raise ValueError("No risk matrix available")

        # Calculate score from matrix
        likelihood_index = ord(likelihood.upper()) - ord("A")
        if 0 <= likelihood_index < 5 and 1 <= severity <= 5:
            score = matrix.matrix_data[severity - 1][likelihood_index]
        else:
            score = 0

        # Get risk band
        band = matrix.get_risk_band(score)
        
        return score, band, matrix.name

    async def create_risk_ranking(
        self,
        deviation_id: str,
        category: str,
        severity: int,
        likelihood: str,
        consequence_id: str | None = None,
        matrix_id: str | None = None,
    ) -> RiskRanking:
        """Create a risk ranking for a deviation."""
        score, band, matrix_name = await self.calculate_risk_score(
            severity, likelihood, matrix_id
        )

        ranking = RiskRanking(
            deviation_id=deviation_id,
            consequence_id=consequence_id,
            category=category,
            severity=severity,
            likelihood=likelihood,
            risk_score=score,
            risk_band=band,
        )
        self.db.add(ranking)
        await self.db.flush()
        await self.db.refresh(ranking)
        return ranking

    async def get_deviation_risk_rankings(
        self,
        deviation_id: str,
    ) -> list[RiskRanking]:
        """Get all risk rankings for a deviation."""
        result = await self.db.execute(
            select(RiskRanking).where(RiskRanking.deviation_id == deviation_id)
        )
        return list(result.scalars().all())

    async def update_risk_ranking(
        self,
        ranking_id: str,
        severity: int | None = None,
        likelihood: str | None = None,
    ) -> RiskRanking | None:
        """Update a risk ranking and recalculate score."""
        result = await self.db.execute(
            select(RiskRanking).where(RiskRanking.id == ranking_id)
        )
        ranking = result.scalar_one_or_none()
        if not ranking:
            return None

        if severity is not None:
            ranking.severity = severity
        if likelihood is not None:
            ranking.likelihood = likelihood

        # Recalculate score
        score, band, _ = await self.calculate_risk_score(
            ranking.severity,
            ranking.likelihood,
        )
        ranking.risk_score = score
        ranking.risk_band = band
        ranking.updated_at = datetime.now(timezone.utc)

        await self.db.flush()
        await self.db.refresh(ranking)
        return ranking

    async def delete_risk_ranking(self, ranking_id: str) -> bool:
        """Delete a risk ranking."""
        result = await self.db.execute(
            select(RiskRanking).where(RiskRanking.id == ranking_id)
        )
        ranking = result.scalar_one_or_none()
        if ranking:
            await self.db.delete(ranking)
            await self.db.flush()
            return True
        return False

    # Matrix Override operations
    async def create_override(
        self,
        override_data: RiskMatrixOverride,
    ) -> RiskMatrixOverride:
        """Create a study-specific risk matrix override."""
        override = RiskMatrixOverride(
            matrix_id=override_data.matrix_id,
            study_id=override_data.study_id,
            severity=override_data.severity,
            likelihood=override_data.likelihood,
            new_score=override_data.new_score,
            new_band=override_data.new_band,
            reason=override_data.reason,
        )
        self.db.add(override)
        await self.db.flush()
        await self.db.refresh(override)
        return override

    async def get_study_overrides(self, study_id: str) -> list[RiskMatrixOverride]:
        """Get all overrides for a study."""
        result = await self.db.execute(
            select(RiskMatrixOverride).where(
                RiskMatrixOverride.study_id == study_id
            )
        )
        return list(result.scalars().all())