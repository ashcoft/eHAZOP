"""WebSocket route for real-time collaboration."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Any

from ehazop_backend.app.core.websocket import manager
from ehazop_backend.app.core.security import verify_access_token

router = APIRouter(tags=["WebSocket"])


@router.websocket("/studies/{study_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    study_id: str,
    token: str = Query(...),
):
    """WebSocket endpoint for real-time study collaboration."""
    # Verify token
    try:
        payload = verify_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001)
            return
    except Exception:
        await websocket.close(code=4001)
        return

    # Connect to study room
    await manager.connect(websocket, study_id)
    
    # Update presence
    manager.update_presence(study_id, user_id, {
        "connected_at": str(websocket.client),
        "role": payload.get("role", "participant"),
    })

    # Broadcast user joined
    await manager.broadcast(
        study_id,
        {
            "type": "user_joined",
            "user_id": user_id,
            "presence": manager.get_presence(study_id),
        },
        exclude=websocket,
    )

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            # Handle message types
            msg_type = data.get("type")
            
            if msg_type == "presence_update":
                manager.update_presence(study_id, user_id, data.get("data", {}))
                await manager.broadcast(
                    study_id,
                    {
                        "type": "presence_update",
                        "user_id": user_id,
                        "data": data.get("data", {}),
                    },
                    exclude=websocket,
                )
            
            elif msg_type == "lock_row":
                deviation_id = data.get("deviation_id")
                if manager.acquire_lock(study_id, deviation_id, user_id):
                    await manager.broadcast(
                        study_id,
                        {
                            "type": "row_locked",
                            "deviation_id": deviation_id,
                            "user_id": user_id,
                        },
                    )
                else:
                    await manager.send_personal(
                        websocket,
                        {
                            "type": "lock_denied",
                            "deviation_id": deviation_id,
                            "locked_by": manager.locks[study_id].get(deviation_id),
                        },
                    )
            
            elif msg_type == "unlock_row":
                deviation_id = data.get("deviation_id")
                if manager.release_lock(study_id, deviation_id, user_id):
                    await manager.broadcast(
                        study_id,
                        {
                            "type": "row_unlocked",
                            "deviation_id": deviation_id,
                            "user_id": user_id,
                        },
                    )
            
            elif msg_type == "deviation_update":
                # Broadcast deviation update
                await manager.broadcast(
                    study_id,
                    {
                        "type": "deviation_update",
                        "deviation_id": data.get("deviation_id"),
                        "user_id": user_id,
                        "data": data.get("data", {}),
                    },
                    exclude=websocket,
                )
            
            elif msg_type == "ping":
                await manager.send_personal(websocket, {"type": "pong"})
            
            else:
                # Unknown message type - broadcast as-is
                await manager.broadcast(
                    study_id,
                    {**data, "user_id": user_id},
                    exclude=websocket,
                )

    except WebSocketDisconnect:
        # User disconnected
        manager.disconnect(websocket, study_id)
        manager.remove_presence(study_id, user_id)
        
        # Release all locks held by this user
        locks = list(manager.locks[study_id].items())
        for deviation_id, locked_by in locks:
            if locked_by == user_id:
                manager.release_lock(study_id, deviation_id, user_id)
        
        # Broadcast user left
        await manager.broadcast(
            study_id,
            {
                "type": "user_left",
                "user_id": user_id,
                "presence": manager.get_presence(study_id),
            },
        )


@router.get("/studies/{study_id}/presence")
async def get_presence(
    study_id: str,
):
    """Get current presence data for a study."""
    return {
        "presence": manager.get_presence(study_id),
        "locks": manager.get_locks(study_id),
    }