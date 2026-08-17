from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID

from BE.models.conservation_members import ConversationMember
from BE.models.messages import Message
from BE.repositories.conversation_repository import ConversationRepository
from BE.repositories.message_repository import MessageRepository
from BE.schemas.messages import ReadStatusResponse


class ReadStatusBroadcaster(Protocol):
    async def broadcast(
        self, conversation_id: UUID, payload: dict[str, object]
    ) -> None:
        """Broadcast a read-receipt event to connected conversation members."""


class ReadConversationNotFoundError(Exception):
    """Raised when a read-status operation targets an unknown conversation."""


class ReadAccessError(Exception):
    """Raised when a user is not a conversation member."""


class ReadMessageNotFoundError(Exception):
    """Raised when the read cursor is not a message in the conversation."""


class ReadStatusService:
    """Business operations for conversation read receipts and unread counts."""

    def __init__(
        self,
        conversation_repository: ConversationRepository,
        message_repository: MessageRepository,
        broadcaster: ReadStatusBroadcaster,
    ) -> None:
        self._conversation_repository = conversation_repository
        self._message_repository = message_repository
        self._broadcaster = broadcaster

    async def mark_as_read(
        self, conversation_id: UUID, user_id: UUID, message_id: UUID
    ) -> ReadStatusResponse:
        membership = await self._require_membership(conversation_id, user_id)
        message = await self._get_message(conversation_id, message_id)
        current_last_read = await self._get_current_last_read(membership)
        if current_last_read is not None and not self._is_after(
            message, current_last_read
        ):
            return ReadStatusResponse.model_validate(membership)

        updated_membership = await self._conversation_repository.update_last_read(
            membership, message.id, datetime.now(timezone.utc)
        )
        response = ReadStatusResponse.model_validate(updated_membership)
        await self._broadcaster.broadcast(
            conversation_id,
            {
                "event": "message.read",
                "user_id": str(user_id),
                "last_read_message_id": str(message.id),
                "last_read_at": response.last_read_at.isoformat()
                if response.last_read_at is not None
                else None,
            },
        )
        return response

    async def count_unread(self, conversation_id: UUID, user_id: UUID) -> int:
        membership = await self._require_membership(conversation_id, user_id)
        last_read_message = await self._get_current_last_read(membership)
        return await self._message_repository.count_unread(
            conversation_id, user_id, last_read_message
        )

    async def _require_membership(
        self, conversation_id: UUID, user_id: UUID
    ) -> ConversationMember:
        conversation = await self._conversation_repository.get_by_id(conversation_id)
        if conversation is None:
            raise ReadConversationNotFoundError("Conversation was not found.")
        membership = await self._conversation_repository.get_member(
            conversation_id, user_id
        )
        if membership is None:
            raise ReadAccessError("You are not a member of this conversation.")
        return membership

    async def _get_message(self, conversation_id: UUID, message_id: UUID) -> Message:
        message = await self._message_repository.get_by_id(message_id)
        if message is None or message.conversation_id != conversation_id:
            raise ReadMessageNotFoundError(
                "Message was not found in this conversation."
            )
        return message

    async def _get_current_last_read(
        self, membership: ConversationMember
    ) -> Message | None:
        if membership.last_read_message_id is None:
            return None
        return await self._message_repository.get_by_id(
            membership.last_read_message_id
        )

    @staticmethod
    def _is_after(candidate: Message, reference: Message) -> bool:
        return (candidate.created_at, candidate.id) > (
            reference.created_at,
            reference.id,
        )
