import asyncio
from uuid import UUID

import pytest
import fakeredis.aioredis

from BE.websocket import manager as manager_module
from BE.websocket import router as router_module


class FakeWebSocket:
    def __init__(self, incoming: str | None = None) -> None:
        self.incoming = incoming
        self.sent: list[dict[str, object]] = []
        self.closed_code: int | None = None

    async def receive_text(self) -> str:
        if self.incoming is None:
            await asyncio.sleep(1)
            return ""
        return self.incoming

    async def send_json(self, payload: dict[str, object]) -> None:
        self.sent.append(payload)

    async def close(self, code: int | None = None) -> None:
        self.closed_code = code


@pytest.mark.asyncio
async def test_websocket_auth_timeout_closes_with_4401(monkeypatch) -> None:
    websocket = FakeWebSocket()
    monkeypatch.setattr(router_module, "WS_AUTH_TIMEOUT_SECONDS", 0.001)

    assert await router_module._authenticate(websocket) is None
    assert websocket.closed_code == 4401
    assert websocket.sent == [{"event": "error", "detail": "Authentication timed out."}]


@pytest.mark.asyncio
async def test_connection_manager_sends_to_all_connections_and_can_exclude_one() -> None:
    manager = manager_module.ConnectionManager()
    user_id = UUID("00000000-0000-0000-0000-000000000010")
    first = FakeWebSocket()
    second = FakeWebSocket()
    manager.connect(user_id, "connection-a", first)
    manager.connect(user_id, "connection-b", second)

    await manager.send_to_user(user_id, {"event": "test"}, "connection-a")

    assert first.sent == []
    assert second.sent == [{"event": "test"}]


@pytest.mark.asyncio
async def test_pubsub_delivers_event_between_manager_instances() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    first_manager = manager_module.ConnectionManager(redis)
    second_manager = manager_module.ConnectionManager(redis)
    user_id = UUID("00000000-0000-0000-0000-000000000011")
    websocket = FakeWebSocket()
    second_manager.connect(user_id, "connection-b", websocket)

    await first_manager.start_subscriber()
    await second_manager.start_subscriber()
    await asyncio.sleep(0.05)
    await first_manager._publish({user_id}, {"event": "cross-worker"})
    await asyncio.sleep(0.1)

    assert websocket.sent == [{"event": "cross-worker"}]
    await first_manager.stop_subscriber()
    await second_manager.stop_subscriber()
    await redis.aclose()
