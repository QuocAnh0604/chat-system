from collections import defaultdict
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    """Track active WebSocket connections by conversation."""

    def __init__(self) -> None:
        self._connections: dict[UUID, set[WebSocket]] = defaultdict(set)

    async def connect(self, conversation_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[conversation_id].add(websocket)

    def disconnect(self, conversation_id: UUID, websocket: WebSocket) -> None:
        connections = self._connections.get(conversation_id)
        if connections is None:
            return

        connections.discard(websocket)
        if not connections:
            self._connections.pop(conversation_id, None)

    async def broadcast(self, conversation_id: UUID, payload: dict[str, object]) -> None:
        """Send a persisted message event to connected conversation members."""
        for websocket in self._connections.get(conversation_id, set()).copy():
            try:
                await websocket.send_json(payload)
            except (RuntimeError, WebSocketDisconnect):
                self.disconnect(conversation_id, websocket)


connection_manager = ConnectionManager()
