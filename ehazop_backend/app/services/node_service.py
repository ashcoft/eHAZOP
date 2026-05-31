"""Node management service."""

from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ehazop_backend.app.models.hazard import Node, Deviation
from ehazop_backend.app.models.user import Study
from ehazop_backend.app.schemas.hazard import NodeCreate, NodeUpdate


class NodeService:
    """Service for managing HAZOP nodes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_node(self, node_data: NodeCreate) -> Node:
        """Create a new node."""
        node = Node(
            study_id=node_data.study_id,
            reference=node_data.reference,
            name=node_data.name,
            description=node_data.description,
            design_intent=node_data.design_intent,
            equipment_type=node_data.equipment_type,
            drawing_reference=node_data.drawing_reference,
            node_category=node_data.node_category,
            operational_mode=node_data.operational_mode,
            order_index=node_data.order_index,
        )
        self.db.add(node)
        await self.db.flush()
        await self.db.refresh(node)
        return node

    async def get_node_by_id(self, node_id: str) -> Node | None:
        """Get a node by ID."""
        result = await self.db.execute(select(Node).where(Node.id == node_id))
        return result.scalar_one_or_none()

    async def list_nodes(
        self,
        study_id: str,
        page: int = 1,
        page_size: int = 50,
        is_active: bool | None = True,
    ) -> tuple[list[Node], int]:
        """List nodes for a study with pagination."""
        query = select(Node).where(Node.study_id == study_id)
        count_query = select(func.count(Node.id)).where(Node.study_id == study_id)

        if is_active is not None:
            query = query.where(Node.is_active == is_active)
            count_query = count_query.where(Node.is_active == is_active)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Node.order_index, Node.reference)
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        nodes = list(result.scalars().all())

        return nodes, total

    async def update_node(
        self,
        node_id: str,
        node_data: NodeUpdate,
    ) -> Node | None:
        """Update a node."""
        node = await self.get_node_by_id(node_id)
        if not node:
            return None

        update_data = node_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(node, field, value)

        node.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(node)
        return node

    async def delete_node(self, node_id: str) -> bool:
        """Soft delete a node."""
        node = await self.get_node_by_id(node_id)
        if not node:
            return False

        node.is_active = False
        node.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True

    async def reorder_nodes(self, study_id: str, node_order: list[str]) -> None:
        """Reorder nodes within a study."""
        for index, node_id in enumerate(node_order):
            result = await self.db.execute(
                select(Node).where(Node.id == node_id, Node.study_id == study_id)
            )
            node = result.scalar_one_or_none()
            if node:
                node.order_index = index

        await self.db.flush()

    async def get_node_with_deviation_count(self, node_id: str) -> Node | None:
        """Get node with count of deviations."""
        node = await self.get_node_by_id(node_id)
        if not node:
            return None

        count_result = await self.db.execute(
            select(func.count(Deviation.id)).where(Deviation.node_id == node_id)
        )
        # Attach the count as an attribute (won't be persisted)
        node.deviation_count = count_result.scalar() or 0
        return node