from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import UUID

import fakeredis.aioredis
import pytest

from BE.schemas.messages import MessageResponse
from BE.services.message_cache import MessageCache
from BE.services.message_service import MessageAccessError, MessageService


def build_response(message_id: str, conversation_id: UUID) -> MessageResponse:
    return MessageResponse(
        id=UUID(message_id),
        conversation_id=conversation_id,
        sender_id=UUID("00000000-0000-0000-0000-000000000002"),
        reply_to_message_id=None,
        content=message_id,
        type="text",
        status="sent",
        client_message_id=None,
        created_at=datetime.now(timezone.utc),
        edited_at=None,
    )


@pytest.mark.asyncio
async def test_message_cache_set_push_get_and_invalidate() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    cache = MessageCache(redis)
    conversation_id = UUID("00000000-0000-0000-0000-000000000003")
    first = build_response("00000000-0000-0000-0000-000000000011", conversation_id)
    second = build_response("00000000-0000-0000-0000-000000000012", conversation_id)

    await cache.set_recent(conversation_id, [first])
    await cache.push_message(second)
    cached = await cache.get_recent(conversation_id)

    assert cached is not None
    assert [item.id for item in cached] == [second.id, first.id]

    await cache.invalidate(conversation_id)
    assert await cache.get_recent(conversation_id) is None
    await redis.aclose()


@pytest.mark.asyncio
async def test_message_service_checks_membership_before_cache() -> None:
    message_repository = AsyncMock()
    conversation_repository = AsyncMock()
    conversation_repository.get_by_id.return_value = object()
    conversation_repository.get_member.return_value = None
    cache = AsyncMock()
    service = MessageService(
        message_repository,
        conversation_repository,
        AsyncMock(),
        AsyncMock(),
        AsyncMock(),
        cache,
    )

    with pytest.raises(MessageAccessError):
        await service.get_messages(
            UUID("00000000-0000-0000-0000-000000000003"),
            UUID("00000000-0000-0000-0000-000000000002"),
            None,
            50,
        )

    cache.get_recent.assert_not_awaited()


@pytest.mark.asyncio
async def test_message_service_cache_hit_skips_message_select() -> None:
    conversation_id = UUID("00000000-0000-0000-0000-000000000003")
    user_id = UUID("00000000-0000-0000-0000-000000000002")
    cached_message = build_response(
        "00000000-0000-0000-0000-000000000013", conversation_id
    )
    message_repository = AsyncMock()
    conversation_repository = AsyncMock()
    conversation_repository.get_by_id.return_value = object()
    conversation_repository.get_member.return_value = object()
    cache = AsyncMock()
    cache.get_recent.return_value = [cached_message]
    service = MessageService(
        message_repository,
        conversation_repository,
        AsyncMock(),
        AsyncMock(),
        AsyncMock(),
        cache,
    )

    result = await service.get_messages(conversation_id, user_id, None, 50)

    assert result.messages[0].id == cached_message.id
    message_repository.list_for_conversation.assert_not_awaited()
