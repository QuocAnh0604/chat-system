from uuid import UUID

from BE.core.security import hash_password, verify_password
from BE.models.users import User
from BE.repositories.refresh_token_repository import RefreshTokenRepository
from BE.repositories.user_repository import UserRepository
from BE.schemas.users import PasswordChange, UserCreate, UserUpdate


class UserAlreadyExistsError(Exception):
    """Raised when a username or email address is already registered."""


class UserNotFoundError(Exception):
    """Raised when a requested user account does not exist."""


class NoProfileChangesError(Exception):
    """Raised when a profile update request contains no changes."""


class InvalidCurrentPasswordError(Exception):
    """Raised when the current password does not match the account password."""


class UserService:
    """Business operations for user accounts."""

    def __init__(
        self,
        user_repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository | None = None,
    ) -> None:
        self._user_repository = user_repository
        self._refresh_token_repository = refresh_token_repository

    async def register(self, payload: UserCreate) -> User:
        existing_user = await self._user_repository.get_by_username_or_email(
            payload.username, str(payload.email)
        )
        if existing_user is not None:
            raise UserAlreadyExistsError("Username or email is already registered.")

        user = await self._user_repository.create(
            username=payload.username,
            display_name=payload.display_name,
            email=str(payload.email),
            password_hash=hash_password(payload.password),
            avatar_url=payload.avatar_url,
        )
        if user is None:
            raise UserAlreadyExistsError("Username or email is already registered.")
        return user

    async def get_profile(self, user_id: UUID) -> User:
        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError("User account was not found.")
        return user

    async def search_users(self, query: str, limit: int) -> list[User]:
        return await self._user_repository.search_by_display_name(query, limit)

    async def update_profile(self, user_id: UUID, payload: UserUpdate) -> User:
        values = payload.model_dump(exclude_unset=True)
        if not values:
            raise NoProfileChangesError("At least one profile field must be provided.")
        user = await self.get_profile(user_id)
        return await self._user_repository.update_profile(user, values)

    async def change_password(self, user_id: UUID, payload: PasswordChange) -> None:
        user = await self.get_profile(user_id)
        if not verify_password(payload.current_password, user.password_hash):
            raise InvalidCurrentPasswordError("Current password is incorrect.")

        await self._user_repository.update_password(user, hash_password(payload.new_password))
        if self._refresh_token_repository is not None:
            await self._refresh_token_repository.revoke_all_for_user(user.id)

    async def update_avatar(self, user_id: UUID, avatar_url: str) -> User:
        user = await self.get_profile(user_id)
        return await self._user_repository.update_profile(
            user, {"avatar_url": avatar_url}
        )
