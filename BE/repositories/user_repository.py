from uuid import UUID

from datetime import datetime

from sqlalchemy import or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from BE.models.users import User


class UserRepository:
    """Persist and retrieve users without applying business rules."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_username_or_email(
        self, username: str, email: str
    ) -> User | None:
        statement = select(User).where(
            or_(User.username == username, User.email == email)
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self._session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_ids(self, user_ids: set[UUID]) -> list[User]:
        if not user_ids:
            return []
        result = await self._session.execute(select(User).where(User.id.in_(user_ids)))
        return list(result.scalars().all())

    async def update_last_seen(self, user_id: UUID, value: datetime) -> None:
        statement = update(User).where(User.id == user_id).values(last_seen=value)
        await self._session.execute(statement)
        await self._session.commit()

    async def search_by_display_name(
        self, query: str, limit: int
    ) -> list[User]:
        """Find active users whose display name contains the query."""
        statement = (
            select(User)
            .where(User.is_active.is_(True), User.display_name.like(f"%{query}%"))
            .order_by(User.display_name.asc())
            .limit(limit)
        )
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def get_active_ids(self, user_ids: set[UUID]) -> set[UUID]:
        if not user_ids:
            return set()
        result = await self._session.execute(
            select(User.id).where(User.id.in_(user_ids), User.is_active.is_(True))
        )
        return set(result.scalars().all())

    async def update_profile(self, user: User, values: dict[str, str | None]) -> User:
        for field, value in values.items():
            setattr(user, field, value)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def update_password(self, user: User, password_hash: str) -> None:
        user.password_hash = password_hash
        await self._session.commit()

    async def create(
        self,
        *,
        username: str,
        display_name: str,
        email: str,
        password_hash: str,
        avatar_url: str | None = None,
    ) -> User | None:
        user = User(
            username=username,
            display_name=display_name,
            email=email,
            password_hash=password_hash,
            avatar_url=avatar_url,
        )
        self._session.add(user)
        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            return None
        await self._session.refresh(user)
        return user
