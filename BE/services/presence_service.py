from datetime import datetime, timezone
from uuid import UUID

from redis.asyncio import Redis

from BE.models.users import User
from BE.repositories.user_repository import UserRepository
from BE.schemas.users import PresenceStatus

PRESENCE_TTL_SECONDS = 30


class PresenceService:
    def __init__(self, repository: UserRepository, redis: Redis) -> None:
        self._repository = repository
        self._redis = redis

    @staticmethod
    def key(user_id: UUID) -> str:
        return f"presence:{user_id}"

    async def mark_online(self, user_id: UUID) -> None:
        await self._redis.set(
            self.key(user_id), "online", ex=PRESENCE_TTL_SECONDS
        )

    async def refresh_presence(self, user_id: UUID) -> None:
        await self._redis.expire(self.key(user_id), PRESENCE_TTL_SECONDS)

    async def mark_offline(self, user_id: UUID) -> None:
        await self._redis.delete(self.key(user_id))
        await self._repository.update_last_seen(user_id, datetime.now(timezone.utc))

    async def is_online(self, user_id: UUID) -> bool:
        return bool(await self._redis.exists(self.key(user_id)))

    async def get_statuses(self, users: list[User]) -> list[PresenceStatus]:
        if not users:
            return []
        keys = [self.key(user.id) for user in users]
        values = await self._redis.mget(keys)
        return [
            PresenceStatus(
                user_id=user.id,
                is_online=values[index] is not None,
                last_seen_at=None if values[index] is not None else user.last_seen,
            )
            for index, user in enumerate(users)
        ]