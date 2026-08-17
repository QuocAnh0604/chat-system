import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from BE.models.refresh_tokens import RefreshToken


class RefreshTokenRepository:
    """Database operations for refresh-token sessions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, *, token_id: uuid.UUID, user_id: uuid.UUID, expires_at: datetime
    ) -> RefreshToken:
        refresh_token = RefreshToken(
            id=token_id,
            user_id=user_id,
            expires_at=expires_at,
        )
        self._session.add(refresh_token)
        await self._session.commit()
        await self._session.refresh(refresh_token)
        return refresh_token

    async def get_active(self, token_id: uuid.UUID) -> RefreshToken | None:
        statement = select(RefreshToken).where(
            RefreshToken.id == token_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def revoke(self, refresh_token: RefreshToken) -> None:
        refresh_token.revoked_at = datetime.now(timezone.utc)
        await self._session.commit()

    async def rotate(
        self,
        current_token: RefreshToken,
        *,
        token_id: uuid.UUID,
        user_id: uuid.UUID,
        expires_at: datetime,
    ) -> None:
        """Revoke a session and create its replacement in one transaction."""
        current_token.revoked_at = datetime.now(timezone.utc)
        self._session.add(
            RefreshToken(id=token_id, user_id=user_id, expires_at=expires_at)
        )
        await self._session.commit()

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        statement = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await self._session.execute(statement)
        await self._session.commit()
