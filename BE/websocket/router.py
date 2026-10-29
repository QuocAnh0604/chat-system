import asyncio
import json
from uuid import UUID, uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from BE.config.database import AsyncSessionLocal
from BE.config.redis import redis_client
from BE.config.settings import (
    WS_AUTH_TIMEOUT_SECONDS,
    WS_MAX_PENDING_AUTHENTICATIONS,
)
from BE.core.security import ExpiredTokenError, decode_token
from BE.repositories.conversation_repository import ConversationRepository
from BE.repositories.message_repository import MessageRepository
from BE.repositories.user_repository import UserRepository
from BE.schemas.messages import MessageCreate, MessageResponse
from BE.services.message_service import (
    InvalidMessageContentError,
    MessageAccessError,
    MessageConversationNotFoundError,
    MessageService,
    MessageTargetNotFoundError,
)
from BE.services.message_cache import MessageCache
from BE.services.presence_service import PresenceService
from BE.services.upload_service import UploadService
from BE.services.user_service import UserNotFoundError, UserService
from BE.websocket.manager import connection_manager

router = APIRouter(tags=["WebSocket"])
_pending_authentications = 0
_pending_auth_lock = asyncio.Lock()


async def _send_auth_error(
    websocket: WebSocket,
    detail: str,
    expired: bool = False,
) -> None:
    if expired:
        await websocket.send_json({"event": "auth.expired"})
    else:
        await websocket.send_json({"event": "error", "detail": detail})
    await websocket.close(code=4401)


async def _authenticate(websocket: WebSocket) -> UUID | None:
    global _pending_authentications

    async with _pending_auth_lock:
        if _pending_authentications >= WS_MAX_PENDING_AUTHENTICATIONS:
            await websocket.close(code=4401)
            return None
        _pending_authentications += 1

    try:
        try:
            raw_payload = await asyncio.wait_for(
                websocket.receive_text(), timeout=WS_AUTH_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            await _send_auth_error(websocket, "Authentication timed out.")
            return None
        except WebSocketDisconnect:
            return None

        try:
            payload = json.loads(raw_payload)
            if (
                not isinstance(payload, dict)
                or payload.get("type") != "auth"
                or not payload.get("token")
            ):
                await _send_auth_error(websocket, "Authentication is required.")
                return None

            token_payload = decode_token(payload["token"], "access")
            user_id = UUID(token_payload["sub"])
        except ExpiredTokenError:
            await _send_auth_error(websocket, "Token has expired.", expired=True)
            return None
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            await _send_auth_error(websocket, "Invalid authentication token.")
            return None

        async with AsyncSessionLocal() as session:
            try:
                user = await UserService(UserRepository(session)).get_profile(user_id)
            except UserNotFoundError:
                await _send_auth_error(websocket, "User account was not found.")
                return None
            if not user.is_active:
                await _send_auth_error(websocket, "User account is inactive.")
                return None
        return user_id
    finally:
        async with _pending_auth_lock:
            _pending_authentications -= 1


def _message_service(session) -> MessageService:
    return MessageService(
        MessageRepository(session),
        ConversationRepository(session),
        connection_manager,
        UploadService(),
        UserRepository(session),
        MessageCache(redis_client),
    )


async def _send_message(
    websocket: WebSocket,
    user_id: UUID,
    connection_id: str,
    payload: dict[str, object],
) -> None:
    client_message_id = payload.get("client_message_id")
    try:
        message_payload = MessageCreate.model_validate(
            {
                "content": payload.get("content"),
                "client_message_id": client_message_id,
            }
        )
        conversation_value = payload.get("conversation_id")
        target_value = payload.get("target_user_id")
        if (conversation_value is None) == (target_value is None):
            raise ValueError(
                "Provide exactly one of conversation_id or target_user_id."
            )

        async with AsyncSessionLocal() as session:
            service = _message_service(session)
            if conversation_value is not None:
                message = await service.send_message(
                    UUID(str(conversation_value)),
                    user_id,
                    message_payload,
                    exclude_connection_id=connection_id,
                )
            else:
                message = await service.send_message_to_user(
                    user_id,
                    message_payload,
                    UUID(str(target_value)),
                    exclude_connection_id=connection_id,
                )

        await websocket.send_json(
            {
                "event": "message.ack",
                "client_message_id": client_message_id,
                "message": MessageResponse.model_validate(message).model_dump(
                    mode="json"
                ),
            }
        )
    except ValidationError as exc:
        detail = exc.errors()[0].get("msg", "Invalid message payload.")
        await websocket.send_json(
            {"event": "error", "client_message_id": client_message_id, "detail": detail}
        )
    except (
        ValueError,
        InvalidMessageContentError,
        MessageConversationNotFoundError,
        MessageAccessError,
        MessageTargetNotFoundError,
    ) as exc:
        await websocket.send_json(
            {
                "event": "error",
                "client_message_id": client_message_id,
                "detail": str(exc),
            }
        )


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    user_id = await _authenticate(websocket)
    if user_id is None:
        return

    connection_id = str(uuid4())
    presence_service = PresenceService(
        None, redis_client, session_factory=AsyncSessionLocal
    )
    connection_manager.connect(user_id, connection_id, websocket)
    became_online = await presence_service.connect(user_id, connection_id)
    await websocket.send_json({"event": "connected"})
    if became_online:
        await connection_manager.broadcast_presence(
            user_id,
            {
                "event": "presence.updated",
                "user_id": str(user_id),
                "is_online": True,
                "last_seen_at": None,
            },
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
            if not isinstance(payload, dict):
                await websocket.send_json(
                    {"event": "error", "detail": "Payload must be a JSON object."}
                )
                continue

            if payload.get("type") == "ping":
                await presence_service.heartbeat(user_id, connection_id)
                await websocket.send_json({"event": "pong"})
                continue
            if payload.get("type") == "message.send":
                await _send_message(websocket, user_id, connection_id, payload)
                continue
            await websocket.send_json(
                {"event": "error", "detail": "Unsupported message type."}
            )
    except WebSocketDisconnect:
        pass
    finally:
        connection_manager.disconnect(user_id, connection_id)
        became_offline = await presence_service.disconnect(user_id, connection_id)
        if became_offline:
            await connection_manager.broadcast_presence(
                user_id,
                {
                    "event": "presence.updated",
                    "user_id": str(user_id),
                    "is_online": False,
                    "last_seen_at": presence_service.current_time().isoformat(),
                },
            )
