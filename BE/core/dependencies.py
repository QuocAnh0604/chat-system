import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from BE.config.database import get_db
from BE.core.security import decode_token
from BE.models.users import User
from BE.repositories.user_repository import UserRepository
from BE.services.user_service import UserNotFoundError, UserService

_bearer_scheme = HTTPBearer(auto_error=False)
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]
BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)
]


async def get_current_user(
    credentials: BearerCredentials, session: DatabaseSession
) -> User:
    """Resolve the active user represented by an access Bearer token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials are required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials, "access")
        user_id = uuid.UUID(payload["sub"])
        user = await UserService(UserRepository(session)).get_profile(user_id)
    except (KeyError, UserNotFoundError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive.",
        )
    return user
