"""Hazard and node routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ehazop_backend.app.core.database import get_db
from ehazop_backend.app.core.dependencies import get_current_user
from ehazop_backend.app.schemas.hazard import (
    NodeCreate,
    NodeUpdate,
    NodeResponse,
    NodeListResponse,
)
from ehazop_backend.app.services.node_service import NodeService

router = APIRouter(tags=["Nodes"])


@router.get("/studies/{study_id}/nodes", response_model=NodeListResponse)
async def list_nodes(
    study_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    is_active: bool | None = True,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all nodes for a study."""
    node_service = NodeService(db)
    nodes, total = await node_service.list_nodes(
        study_id=study_id,
        page=page,
        page_size=page_size,
        is_active=is_active,
    )

    node_responses = []
    for node in nodes:
        from sqlalchemy import select, func
        from ehazop_backend.app.models.hazard import Deviation
        count_result = await db.execute(
            select(func.count(Deviation.id)).where(Deviation.node_id == node.id)
        )
        deviation_count = count_result.scalar() or 0

        node_responses.append(NodeResponse(
            id=node.id,
            study_id=node.study_id,
            reference=node.reference,
            name=node.name,
            description=node.description,
            design_intent=node.design_intent,
            equipment_type=node.equipment_type,
            drawing_reference=node.drawing_reference,
            node_category=node.node_category,
            operational_mode=node.operational_mode,
            order_index=node.order_index,
            is_active=node.is_active,
            created_at=node.created_at,
            updated_at=node.updated_at,
            deviation_count=deviation_count,
        ))

    return NodeListResponse(
        items=node_responses,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/studies/{study_id}/nodes", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
async def create_node(
    study_id: str,
    node_data: NodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new node in a study."""
    if node_data.study_id != study_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Study ID mismatch",
        )

    node_service = NodeService(db)
    node = await node_service.create_node(node_data)
    return NodeResponse.model_validate(node)


@router.get("/nodes/{node_id}", response_model=NodeResponse)
async def get_node(
    node_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a node by ID."""
    node_service = NodeService(db)
    node = await node_service.get_node_with_deviation_count(node_id)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )

    return NodeResponse(
        id=node.id,
        study_id=node.study_id,
        reference=node.reference,
        name=node.name,
        description=node.description,
        design_intent=node.design_intent,
        equipment_type=node.equipment_type,
        drawing_reference=node.drawing_reference,
        node_category=node.node_category,
        operational_mode=node.operational_mode,
        order_index=node.order_index,
        is_active=node.is_active,
        created_at=node.created_at,
        updated_at=node.updated_at,
        deviation_count=node.deviation_count,
    )


@router.patch("/nodes/{node_id}", response_model=NodeResponse)
async def update_node(
    node_id: str,
    node_data: NodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a node."""
    node_service = NodeService(db)
    node = await node_service.update_node(node_id, node_data)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )

    return NodeResponse.model_validate(node)


@router.delete("/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(
    node_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a node (soft delete)."""
    node_service = NodeService(db)
    success = await node_service.delete_node(node_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )


@router.post("/nodes/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_nodes(
    study_id: str,
    node_order: list[str],
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Reorder nodes within a study."""
    node_service = NodeService(db)
    await node_service.reorder_nodes(study_id, node_order)