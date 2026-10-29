from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import UUID

import fakeredis.aioredis
import pytest

from BE.models.users import User
from BE.services.presence_service import PresenceService


def test_user_id_default_is_callable_and_generates_unique_uuids() -> None:
    default = User.__table__.c.id.default

    assert default is not None
    first = default.arg(None)
    second = default.arg(None)

    assert isinstance(first, UUID)
    assert isinstance(second, UUID)
    assert first != second


@pytest.mark.asyncio
async def test_presence_supports_multiple_connections_and_expiry_recovery() -> None:
    current_time = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    repository = AsyncMock()
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    service = PresenceService(repository, redis, now=lambda: current_time[0])

    await service.connect(user_id, "connection-a")
    await service.connect(user_id, "connection-b")
    assert await service.is_online(user_id)

    current_time[0] = current_time[0].replace(second=5)
    assert await service.disconnect(user_id, "connection-a") is False
    assert await service.is_online(user_id)
    repository.update_last_seen.assert_not_awaited()

    current_time[0] = current_time[0].replace(second=40)
    assert await service.is_online(user_id) is False

    await service.heartbeat(user_id, "connection-b")
    assert await service.is_online(user_id)

    current_time[0] = current_time[0].replace(second=41)
    assert await service.disconnect(user_id, "connection-b") is True
    repository.update_last_seen.assert_awaited_once()

    await redis.aclose()
