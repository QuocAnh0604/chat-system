import json
import logging
from uuid import UUID

from redis.asyncio import Redis

from BE.config.settings import (
    MESSAGE_CACHE_ENABLED,
    MESSAGE_CACHE_SIZE,
    MESSAGE_CACHE_TTL_SECONDS,
)
from BE.schemas.messages import MessageResponse

logger = logging.getLogger(__name__)


class MessageCache:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    @staticmethod
    def key(conversation_id: UUID) -> str:
        return f"chat:recent:{conversation_id}"

    async def get_recent(self, conversation_id: UUID) -> list[MessageResponse] | None:
        if not MESSAGE_CACHE_ENABLED:
            return None
        try:
            values = await self._redis.lrange(
                self.key(conversation_id), 0, MESSAGE_CACHE_SIZE - 1
            )
            if not values:
                return None
            return [MessageResponse.model_validate(json.loads(value)) for value in values]
        except Exception:
            logger.exception("Message cache read failed for conversation %s", conversation_id)
            return None

    async def set_recent(
        self, conversation_id: UUID, messages: list[MessageResponse]
    ) -> None:
        if not MESSAGE_CACHE_ENABLED:
            return
        try:
            values = [message.model_dump_json() for message in messages[:MESSAGE_CACHE_SIZE]]
            if not values:
                return
            key = self.key(conversation_id)
            async with self._redis.pipeline(transaction=False) as pipeline:
                pipeline.delete(key)
                pipeline.rpush(key, *values)
                pipeline.expire(key, MESSAGE_CACHE_TTL_SECONDS)
                await pipeline.execute()
        except Exception:
            logger.exception("Message cache write failed for conversation %s", conversation_id)

    async def push_message(self, message: MessageResponse) -> None:
        if not MESSAGE_CACHE_ENABLED:
            return
        try:
            key = self.key(message.conversation_id)
            if not await self._redis.exists(key):
                return
            async with self._redis.pipeline(transaction=False) as pipeline:
                pipeline.lpush(key, message.model_dump_json())
                pipeline.ltrim(key, 0, MESSAGE_CACHE_SIZE - 1)
                pipeline.expire(key, MESSAGE_CACHE_TTL_SECONDS)
                await pipeline.execute()
        except Exception:
            logger.exception("Message cache push failed for conversation %s", message.conversation_id)

    async def invalidate(self, conversation_id: UUID) -> None:
        if not MESSAGE_CACHE_ENABLED:
            return
        try:
            await self._redis.delete(self.key(conversation_id))
        except Exception:
            logger.exception("Message cache invalidation failed for conversation %s", conversation_id)
