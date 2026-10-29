import asyncio
import json
import logging
import json
import logging
from collections import defaultdict
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect

from BE.config.database import AsyncSessionLocal
from BE.config.redis import redis_client
from BE.config.settings import WS_SEND_TIMEOUT_SECONDS
from BE.repositories.conversation_repository import ConversationRepository


class ConnectionManager:
    """Track authenticated sockets by user and fan out events safely."""

    def __init__(self, redis=redis_client) -> None:
        self._connections: dict[UUID, dict[str, WebSocket]] = defaultdict(dict)
        self._redis = redis
        self._subscriber_task: asyncio.Task[None] | None = None
        self._logger = logging.getLogger(__name__)

    async def start_subscriber(self) -> None:
        if self._subscriber_task is None or self._subscriber_task.done():
            self._subscriber_task = asyncio.create_task(self._subscribe_loop())

    async def stop_subscriber(self) -> None:
        if self._subscriber_task is None:
            return
        self._subscriber_task.cancel()
        try:
            await self._subscriber_task
        except asyncio.CancelledError:
            pass
        self._subscriber_task = None

    async def _subscribe_loop(self) -> None:
        while True:
            pubsub = self._redis.pubsub()
            try:
                await pubsub.subscribe("chat:events")
                while True:
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=True, timeout=1.0
                    )
                    if not message:
                        await asyncio.sleep(0.05)
                        continue
                    try:
                        event = json.loads(message["data"])
                        await self.send_to_users(
                            {UUID(user_id) for user_id in event["recipient_user_ids"]},
                            event["payload"],
                            event.get("exclude_connection_id"),
                        )
                    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                        self._logger.warning("Ignoring malformed chat Pub/Sub event")
            except asyncio.CancelledError:
                raise
            except Exception:
                self._logger.exception("Chat Pub/Sub subscriber disconnected; retrying")
                await asyncio.sleep(1)
            finally:
                try:
                    await pubsub.close()
                except Exception:
                    self._logger.debug("Unable to close Redis Pub/Sub connection", exc_info=True)

    def connect(self, user_id: UUID, connection_id: str, websocket: WebSocket) -> None:
        self._connections[user_id][connection_id] = websocket

    def disconnect(self, user_id: UUID, connection_id: str) -> None:
        connections = self._connections.get(user_id)
        if connections is None:
            return
        connections.pop(connection_id, None)
        if not connections:
            self._connections.pop(user_id, None)

    def _snapshot(
        self,
        user_ids: set[UUID],
        exclude_connection_id: str | None = None,
    ) -> list[tuple[UUID, str, WebSocket]]:
        return [
            (user_id, connection_id, websocket)
            for user_id in user_ids
            for connection_id, websocket in self._connections.get(user_id, {}).items()
            if connection_id != exclude_connection_id
        ]

    async def _send_one(
        self,
        user_id: UUID,
        connection_id: str,
        websocket: WebSocket,
        payload: dict[str, object],
    ) -> None:
        try:
            await asyncio.wait_for(
                websocket.send_json(payload), timeout=WS_SEND_TIMEOUT_SECONDS
            )
        except (asyncio.TimeoutError, RuntimeError, WebSocketDisconnect, OSError):
            self.disconnect(user_id, connection_id)
            try:
                await websocket.close(code=1011)
            except (RuntimeError, WebSocketDisconnect, OSError):
                pass

    async def send_to_user(
        self,
        user_id: UUID,
        payload: dict[str, object],
        exclude_connection_id: str | None = None,
    ) -> None:
        connections = self._snapshot({user_id}, exclude_connection_id)
        await asyncio.gather(
            *[
                self._send_one(user_id, connection_id, websocket, payload)
                for user_id, connection_id, websocket in connections
            ]
        )

    async def send_to_users(
        self,
        user_ids: set[UUID],
        payload: dict[str, object],
        exclude_connection_id: str | None = None,
    ) -> None:
        connections = self._snapshot(user_ids, exclude_connection_id)
        await asyncio.gather(
            *[
                self._send_one(user_id, connection_id, websocket, payload)
                for user_id, connection_id, websocket in connections
            ]
        )

    async def _publish(
        self,
        user_ids: set[UUID],
        payload: dict[str, object],
        exclude_connection_id: str | None = None,
    ) -> None:
        event = {
            "recipient_user_ids": [str(user_id) for user_id in user_ids],
            "payload": payload,
            "exclude_connection_id": exclude_connection_id,
        }
        try:
            await self._redis.publish("chat:events", json.dumps(event))
        except Exception:
            self._logger.warning("Chat Pub/Sub publish failed; using local delivery", exc_info=True)
            await self.send_to_users(user_ids, payload, exclude_connection_id)

    async def broadcast(
        self,
        conversation_id: UUID,
        payload: dict[str, object],
        exclude_connection_id: str | None = None,
    ) -> None:
        async with AsyncSessionLocal() as session:
            member_ids = await ConversationRepository(session).get_member_ids(
                conversation_id
            )
        await self._publish(member_ids, payload, exclude_connection_id)

    async def broadcast_presence(
        self,
        user_id: UUID,
        payload: dict[str, object],
    ) -> None:
        async with AsyncSessionLocal() as session:
            member_ids = await ConversationRepository(
                session
            ).get_user_ids_in_shared_conversations(user_id)
        await self._publish(member_ids, payload)


connection_manager = ConnectionManager()
