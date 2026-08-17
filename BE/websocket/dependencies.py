import uuid

from fastapi import WebSocket, status
from sqlalchemy.ext.asyncio import AsyncSession

from BE.core.security import decode_token
from BE.models.users import User
from BE.repositories.user_repository import UserRepository
from BE.services.user_service import UserNotFoundError, UserService


async def authenticate_websocket(
    websocket: WebSocket, session: AsyncSession
) -> User | None:
    """Return the active user represented by the WebSocket access token."""
    token = websocket.query_params.get("token")
    if token is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None

    try:
        payload = decode_token(token, "access")
        user_id = uuid.UUID(payload["sub"])
        user = await UserService(UserRepository(session)).get_profile(user_id)
    except (KeyError, UserNotFoundError, ValueError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None

    if not user.is_active:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    return user
