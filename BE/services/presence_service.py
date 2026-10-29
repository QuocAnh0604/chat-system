from collections.abc import Callable
from datetime import datetime, timezone
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from BE.config.settings import PRESENCE_TTL_SECONDS
from BE.models.users import User
from BE.repositories.user_repository import UserRepository
from BE.schemas.users import PresenceStatus

LAST_SEEN_TTL_SECONDS = 7 * 24 * 60 * 60


class PresenceService:
    def __init__(
        self,
        repository: UserRepository | None,
        redis: Redis,
        now: Callable[[], datetime] | None = None,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        self._repository = repository
        self._redis = redis
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._session_factory = session_factory

    @staticmethod
    def key(user_id: UUID) -> str:
        return f"presence:{user_id}"

    @staticmethod
    def last_seen_key(user_id: UUID) -> str:
        return f"presence:last_seen:{user_id}"

    def _timestamp(self) -> float:
        current = self._now()
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        return current.timestamp()

    def current_time(self) -> datetime:
        current = self._now()
        return current if current.tzinfo is not None else current.replace(tzinfo=timezone.utc)

    async def _refresh(self, user_id: UUID, connection_id: str) -> bool:
        timestamp = self._timestamp()
        key = self.key(user_id)
        last_seen_key = self.last_seen_key(user_id)
        async with self._redis.pipeline(transaction=False) as pipeline:
            pipeline.zremrangebyscore(key, "-inf", timestamp - PRESENCE_TTL_SECONDS)
            pipeline.zcard(key)
            pipeline.zadd(key, {connection_id: timestamp})
            pipeline.expire(key, PRESENCE_TTL_SECONDS)
            pipeline.set(
                last_seen_key,
                self.current_time().isoformat(),
                ex=LAST_SEEN_TTL_SECONDS,
            )
            result = await pipeline.execute()
        return int(result[1]) == 0

    async def connect(self, user_id: UUID, connection_id: str) -> bool:
        return await self._refresh(user_id, connection_id)

    async def heartbeat(self, user_id: UUID, connection_id: str) -> None:
        # ZADD recreates a connection that was removed by TTL cleanup.
        await self._refresh(user_id, connection_id)

    async def disconnect(self, user_id: UUID, connection_id: str) -> bool:
        timestamp = self._timestamp()
        key = self.key(user_id)
        async with self._redis.pipeline(transaction=False) as pipeline:
            pipeline.zremrangebyscore(key, "-inf", timestamp - PRESENCE_TTL_SECONDS)
            pipeline.zrem(key, connection_id)
            pipeline.zcard(key)
            result = await pipeline.execute()

        remaining_connections = int(result[2])
        if remaining_connections > 0:
            return False

        await self._redis.delete(key)
        if self._session_factory is not None:
            async with self._session_factory() as session:
                await UserRepository(session).update_last_seen(
                    user_id, self.current_time()
                )
        else:
            await self._repository.update_last_seen(user_id, self.current_time())
        return True

    async def is_online(self, user_id: UUID) -> bool:
        timestamp = self._timestamp()
        key = self.key(user_id)
        async with self._redis.pipeline(transaction=False) as pipeline:
            pipeline.zremrangebyscore(key, "-inf", timestamp - PRESENCE_TTL_SECONDS)
            pipeline.zcard(key)
            pipeline.expire(key, PRESENCE_TTL_SECONDS)
            result = await pipeline.execute()
        return int(result[1]) > 0

    async def get_statuses(self, users: list[User]) -> list[PresenceStatus]:
        if not users:
            return []

        timestamp = self._timestamp()
        async with self._redis.pipeline(transaction=False) as pipeline:
            for user in users:
                key = self.key(user.id)
                pipeline.zremrangebyscore(
                    key, "-inf", timestamp - PRESENCE_TTL_SECONDS
                )
                pipeline.zcard(key)
                pipeline.get(self.last_seen_key(user.id))
                pipeline.expire(key, PRESENCE_TTL_SECONDS)
            values = await pipeline.execute()

        statuses: list[PresenceStatus] = []
        for index, user in enumerate(users):
            online = int(values[index * 4 + 1]) > 0
            stored_last_seen = values[index * 4 + 2]
            last_seen_at = user.last_seen_at
            if stored_last_seen:
                if isinstance(stored_last_seen, bytes):
                    stored_last_seen = stored_last_seen.decode()
                last_seen_at = datetime.fromisoformat(stored_last_seen)
            statuses.append(
                PresenceStatus(
                    user_id=user.id,
                    is_online=online,
                    last_seen_at=None if online else last_seen_at,
                )
            )
        return statuses
