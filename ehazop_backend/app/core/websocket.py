"""WebSocket connection manager for real-time collaboration."""

import json
from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections for live workshop collaboration."""

    def __init__(self):
        # study_id -> list of websocket connections
        self.active_connections: dict[str, list[WebSocket]] = defaultdict(list)
        # study_id -> user_id -> presence info
        self.presence: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
        # study_id -> deviation_id -> user_id (row locks)
        self.locks: dict[str, dict[str, str]] = defaultdict(dict)

    async def connect(self, websocket: WebSocket, study_id: str) -> None:
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        if websocket not in self.active_connections[study_id]:
            self.active_connections[study_id].append(websocket)

    def disconnect(self, websocket: WebSocket, study_id: str) -> None:
        """Remove a WebSocket connection."""
        if websocket in self.active_connections[study_id]:
            self.active_connections[study_id].remove(websocket)
        if not self.active_connections[study_id]:
            del self.active_connections[study_id]

    async def broadcast(
        self,
        study_id: str,
        message: dict[str, Any],
        exclude: WebSocket | None = None,
    ) -> None:
        """Broadcast a message to all connected clients in a study."""
        if study_id not in self.active_connections:
            return

        message_str = json.dumps(message)
        disconnected = []

        for connection in self.active_connections[study_id]:
            if connection == exclude:
                continue
            try:
                await connection.send_text(message_str)
            except Exception:
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn, study_id)

    async def send_personal(
        self,
        websocket: WebSocket,
        message: dict[str, Any],
    ) -> None:
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception:
            pass

    def update_presence(
        self,
        study_id: str,
        user_id: str,
        presence_info: dict[str, Any],
    ) -> None:
        """Update user presence in a study."""
        self.presence[study_id][user_id] = presence_info

    def remove_presence(self, study_id: str, user_id: str) -> None:
        """Remove user presence from a study."""
        if study_id in self.presence and user_id in self.presence[study_id]:
            del self.presence[study_id][user_id]

    def get_presence(self, study_id: str) -> dict[str, dict[str, Any]]:
        """Get all presence data for a study."""
        return self.presence.get(study_id, {})

    def acquire_lock(
        self,
        study_id: str,
        deviation_id: str,
        user_id: str,
    ) -> bool:
        """Attempt to acquire a lock on a deviation row."""
        if deviation_id in self.locks[study_id]:
            return self.locks[study_id][deviation_id] == user_id
        
        self.locks[study_id][deviation_id] = user_id
        return True

    def release_lock(
        self,
        study_id: str,
        deviation_id: str,
        user_id: str,
    ) -> bool:
        """Release a lock on a deviation row."""
        if deviation_id in self.locks[study_id]:
            if self.locks[study_id][deviation_id] == user_id:
                del self.locks[study_id][deviation_id]
                return True
        return False

    def get_locks(self, study_id: str) -> dict[str, str]:
        """Get all active locks for a study."""
        return self.locks.get(study_id, {})


# Global connection manager instance
manager = ConnectionManager()