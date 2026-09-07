from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from BE.config.database import get_db
from BE.core.dependencies import get_current_user
from BE.models.users import User
from BE.repositories.refresh_token_repository import RefreshTokenRepository
from BE.repositories.user_repository import UserRepository
from BE.schemas.users import (
    PasswordChange,
    PresenceStatus,
    UserProfile,
    UserResponse,
    UserUpdate,
)
from BE.config.redis import redis_client
from BE.services.presence_service import PresenceService
from BE.services.user_service import (
    InvalidCurrentPasswordError,
    NoProfileChangesError,
    UserService,
)
from BE.services.upload_service import UploadService

router = APIRouter(prefix="/users", tags=["Users"])
CurrentUser = Annotated[User, Depends(get_current_user)]
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("/search", response_model=list[UserResponse])
async def search_users(
    current_user: CurrentUser,
    session: DatabaseSession,
    q: Annotated[str, Query(min_length=1, max_length=100)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[UserResponse]:
    """Search active users by a display-name substring."""
    del current_user
    users = await UserService(UserRepository(session)).search_users(q, limit)
    return [UserResponse.model_validate(user) for user in users]


@router.get("/presence", response_model=list[PresenceStatus])
async def get_presence(
    user_ids: Annotated[list[UUID], Query(min_length=1, max_length=100)],
    current_user: CurrentUser,
    session: DatabaseSession,
) -> list[PresenceStatus]:
    """Return online and last-seen status for a batch of users."""
    del current_user
    users = await UserRepository(session).get_by_ids(set(user_ids))
    return await PresenceService(UserRepository(session), redis_client).get_statuses(users)


@router.get("/me", response_model=UserProfile)
async def get_profile(current_user: CurrentUser) -> UserProfile:
    """Return the profile of the authenticated user."""
    return UserProfile.model_validate(current_user)


@router.patch("/me", response_model=UserProfile)
async def update_profile(
    payload: UserUpdate,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> UserProfile:
    """Update the authenticated user's display name or avatar URL."""
    service = UserService(UserRepository(session))
    try:
        user = await service.update_profile(current_user.id, payload)
    except NoProfileChangesError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return UserProfile.model_validate(user)


@router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: PasswordChange,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> None:
    """Change a password and revoke the user's refresh-token sessions."""
    service = UserService(UserRepository(session), RefreshTokenRepository(session))
    try:
        await service.change_password(current_user.id, payload)
    except InvalidCurrentPasswordError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc


@router.post("/me/avatar", response_model=UserProfile)
async def upload_avatar(
    file: Annotated[UploadFile, File(...)],
    current_user: CurrentUser,
    session: DatabaseSession,
) -> UserProfile:
    """Upload an image avatar and assign it to the authenticated user."""
    upload_service = UploadService()
    avatar_url = await upload_service.save_avatar(file)
    try:
        user = await UserService(UserRepository(session)).update_avatar(
            current_user.id, avatar_url
        )
    except Exception:
        await upload_service.delete_by_url(avatar_url)
        raise
    return UserProfile.model_validate(user)
