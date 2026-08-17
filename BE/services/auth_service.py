import uuid

from BE.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from BE.models.users import User
from BE.repositories.refresh_token_repository import RefreshTokenRepository
from BE.repositories.user_repository import UserRepository
from BE.schemas.auth import LogoutRequest, RefreshTokenRequest, TokenPair
from BE.schemas.users import UserLogin


class InvalidCredentialsError(Exception):
    """Raised when supplied login credentials cannot be authenticated."""


class InactiveUserError(Exception):
    """Raised when an inactive account attempts to authenticate."""


class InvalidRefreshTokenError(Exception):
    """Raised when a refresh token is invalid, expired, or revoked."""


class AuthenticationService:
    """Business operations for issuing and managing account sessions."""

    def __init__(
        self,
        user_repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
    ) -> None:
        self._user_repository = user_repository
        self._refresh_token_repository = refresh_token_repository

    async def login(self, payload: UserLogin) -> TokenPair:
        user = await self._user_repository.get_by_username(payload.username)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise InvalidCredentialsError("Invalid username or password.")
        if not user.is_active:
            raise InactiveUserError("This account is inactive.")
        return await self._create_token_pair(user)

    async def refresh(self, payload: RefreshTokenRequest) -> TokenPair:
        user_id, token_id = self._parse_refresh_token(payload.refresh_token)
        current_token = await self._refresh_token_repository.get_active(token_id)
        if current_token is None or current_token.user_id != user_id:
            raise InvalidRefreshTokenError("Refresh token is invalid or revoked.")

        user = await self._user_repository.get_by_id(user_id)
        if user is None or not user.is_active:
            raise InvalidRefreshTokenError("Refresh token is invalid or revoked.")

        new_token_id = uuid.uuid4()
        refresh_token, expires_at = create_refresh_token(user.id, new_token_id)
        await self._refresh_token_repository.rotate(
            current_token,
            token_id=new_token_id,
            user_id=user.id,
            expires_at=expires_at,
        )
        return TokenPair(
            access_token=create_access_token(user.id),
            refresh_token=refresh_token,
        )

    async def logout(self, payload: LogoutRequest) -> None:
        user_id, token_id = self._parse_refresh_token(payload.refresh_token)
        refresh_token = await self._refresh_token_repository.get_active(token_id)
        if refresh_token is None or refresh_token.user_id != user_id:
            raise InvalidRefreshTokenError("Refresh token is invalid or revoked.")
        await self._refresh_token_repository.revoke(refresh_token)

    async def _create_token_pair(self, user: User) -> TokenPair:
        token_id = uuid.uuid4()
        refresh_token, expires_at = create_refresh_token(user.id, token_id)
        await self._refresh_token_repository.create(
            token_id=token_id,
            user_id=user.id,
            expires_at=expires_at,
        )
        return TokenPair(
            access_token=create_access_token(user.id),
            refresh_token=refresh_token,
        )

    @staticmethod
    def _parse_refresh_token(token: str) -> tuple[uuid.UUID, uuid.UUID]:
        try:
            payload = decode_token(token, "refresh")
            return uuid.UUID(payload["sub"]), uuid.UUID(payload["jti"])
        except (KeyError, ValueError) as exc:
            raise InvalidRefreshTokenError("Refresh token is invalid or expired.") from exc
