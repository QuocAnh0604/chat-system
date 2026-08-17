import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from BE.config.database import get_db
from BE.repositories.conversation_repository import ConversationRepository
from BE.repositories.user_repository import UserRepository
from BE.services.conversation_service import (
    ConversationAccessError,
    ConversationNotFoundError,
    ConversationService,
)
from BE.websocket.dependencies import authenticate_websocket
from BE.websocket.manager import connection_manager

router = APIRouter(tags=["WebSocket"])
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


def _conversation_service(session: AsyncSession) -> ConversationService:
    return ConversationService(ConversationRepository(session), UserRepository(session))


@router.websocket("/ws/conversations/{conversation_id}")
async def conversation_websocket(
    websocket: WebSocket,
    conversation_id: UUID,
    session: DatabaseSession,
) -> None:
    """Open an authenticated realtime connection for one conversation."""
    current_user = await authenticate_websocket(websocket, session)
    if current_user is None:
        return

    try:
        await _conversation_service(session).ensure_member(
            conversation_id, current_user.id
        )
    except (ConversationNotFoundError, ConversationAccessError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await connection_manager.connect(conversation_id, websocket)
    await websocket.send_json(
        {"event": "connected", "conversation_id": str(conversation_id)}
    )
    try:
        while True:
            try:
                payload = json.loads(await websocket.receive_text())
            except json.JSONDecodeError:
                await websocket.send_json(
                    {"event": "error", "detail": "Payload must be valid JSON."}
                )
                continue

            if payload.get("event") == "ping":
                await websocket.send_json({"event": "pong"})
                continue
            await websocket.send_json(
                {
                    "event": "error",
                    "detail": "Messages must be sent through the HTTP API.",
                }
            )
    except WebSocketDisconnect:
        pass
    finally:
        connection_manager.disconnect(conversation_id, websocket)
