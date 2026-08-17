from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from BE.config.database import get_db
from BE.repositories.user_repository import UserRepository
from BE.repositories.refresh_token_repository import RefreshTokenRepository
from BE.schemas.auth import LogoutRequest, RefreshTokenRequest, TokenPair
from BE.schemas.users import UserCreate, UserLogin, UserResponse
from BE.services.auth_service import (
    AuthenticationService,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)
from BE.services.user_service import UserAlreadyExistsError, UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, session: DatabaseSession) -> UserResponse:
    """Create a user account with a securely hashed password."""
    service = UserService(UserRepository(session))
    try:
        user = await service.register(payload)
    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenPair)
async def login(payload: UserLogin, session: DatabaseSession) -> TokenPair:
    """Authenticate a user and create an access/refresh token pair."""
    service = AuthenticationService(
        UserRepository(session), RefreshTokenRepository(session)
    )
    try:
        return await service.login(payload)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc
    except InactiveUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc


@router.post("/refresh", response_model=TokenPair)
async def refresh_token(
    payload: RefreshTokenRequest, session: DatabaseSession
) -> TokenPair:
    """Rotate a refresh token and return a new access/refresh pair."""
    service = AuthenticationService(
        UserRepository(session), RefreshTokenRepository(session)
    )
    try:
        return await service.refresh(payload)
    except InvalidRefreshTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: LogoutRequest, session: DatabaseSession) -> None:
    """Revoke the submitted refresh-token session."""
    service = AuthenticationService(
        UserRepository(session), RefreshTokenRepository(session)
    )
    try:
        await service.logout(payload)
    except InvalidRefreshTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc
