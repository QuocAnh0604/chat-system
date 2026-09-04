from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol
from uuid import UUID

from fastapi import UploadFile
from BE.models.conservations import Conversation
from BE.models.messages import Message, MessageType
from BE.repositories.conversation_repository import ConversationRepository
from BE.repositories.message_repository import MessageRepository
from BE.repositories.user_repository import UserRepository
from BE.schemas.messages import (
    MessageCreate,
    MessagePageResponse,
    MessageResponse,
    MessageUpdate,
)
from BE.services.upload_service import UploadService


class MessageBroadcaster(Protocol):
    async def broadcast(
        self, conversation_id: UUID, payload: dict[str, object]
    ) -> None:
        """Broadcast an event to connected conversation members."""


class MessageConversationNotFoundError(Exception):
    """Raised when a message operation targets an unknown conversation."""


class MessageAccessError(Exception):
    """Raised when a user is not a member of a conversation."""


class MessageTargetNotFoundError(Exception):
    """Raised when a lazy message targets an unknown or inactive user."""


class MessageCursorError(Exception):
    """Raised when a pagination cursor is not a message in the conversation."""


class MessageNotFoundError(Exception):
    """Raised when a requested message is not in the conversation."""


class InvalidMessageContentError(Exception):
    """Raised when text content contains only whitespace."""


class MessageEditPermissionError(Exception):
    """Raised when a user attempts to change another user's message."""


class MessageDeletePermissionError(Exception):
    """Raised when a user attempts to delete another user's message."""


class AttachmentNotFoundError(Exception):
    """Raised when a message does not contain an available attachment."""


class MessageService:
    """Business operations for sending and managing chat messages."""

    def __init__(
        self,
        message_repository: MessageRepository,
        conversation_repository: ConversationRepository,
        broadcaster: MessageBroadcaster,
        upload_service: UploadService,
        user_repository: UserRepository,
    ) -> None:
        self._message_repository = message_repository
        self._conversation_repository = conversation_repository
        self._broadcaster = broadcaster
        self._upload_service = upload_service
        self._user_repository = user_repository

    async def send_message_to_user(
        self, sender_id: UUID, payload: MessageCreate, target_user_id: UUID
    ) -> Message:
        if sender_id == target_user_id:
            raise MessageTargetNotFoundError("A message target must be another user.")
        target = await self._user_repository.get_by_id(target_user_id)
        if target is None or not target.is_active:
            raise MessageTargetNotFoundError("Message target was not found.")

        conversation = await self._conversation_repository.get_private_between(
            sender_id, target_user_id
        )
        if conversation is None:
            conversation = await self._conversation_repository.create_private(
                sender_id, target_user_id
            )

        message = await self._message_repository.create(
            conversation, sender_id, self._normalized_content(payload.content)
        )
        await self._message_repository.commit()
        await self._broadcast("message.created", message)
        return message

    async def send_message(
        self, conversation_id: UUID, sender_id: UUID, payload: MessageCreate
    ) -> Message:
        conversation = await self._require_membership(conversation_id, sender_id)
        content = self._normalized_content(payload.content)
        message = await self._message_repository.create(
            conversation, sender_id, content
        )
        await self._message_repository.commit()
        await self._broadcast("message.created", message)
        return message

    async def reply_to_message(
        self,
        conversation_id: UUID,
        sender_id: UUID,
        reply_to_message_id: UUID,
        payload: MessageCreate,
    ) -> Message:
        conversation = await self._require_membership(conversation_id, sender_id)
        await self._get_message_in_conversation(conversation_id, reply_to_message_id)
        message = await self._message_repository.create(
            conversation,
            sender_id,
            self._normalized_content(payload.content),
            reply_to_message_id,
        )
        await self._message_repository.commit()
        await self._broadcast("message.created", message)
        return message

    async def send_attachment(
        self,
        conversation_id: UUID,
        sender_id: UUID,
        file: UploadFile,
        message_type: MessageType,
    ) -> Message:
        conversation = await self._require_membership(conversation_id, sender_id)
        attachment = await self._upload_service.save_attachment(file, message_type)
        try:
            message = await self._message_repository.create(
                conversation,
                sender_id,
                attachment.url,
                message_type=message_type,
            )
            await self._message_repository.commit()
        except Exception:
            await self._upload_service.delete_attachment(attachment.url)
            raise
        await self._broadcast("message.created", message)
        return message

    async def edit_message(
        self,
        conversation_id: UUID,
        user_id: UUID,
        message_id: UUID,
        payload: MessageUpdate,
    ) -> Message:
        await self._require_membership(conversation_id, user_id)
        message = await self._get_message_in_conversation(conversation_id, message_id)
        if message.sender_id != user_id:
            raise MessageEditPermissionError("Only the sender can edit this message.")
        updated_message = await self._message_repository.update_content(
            message,
            self._normalized_content(payload.content),
            datetime.now(timezone.utc),
        )
        await self._broadcast("message.updated", updated_message)
        return updated_message

    async def delete_message(
        self, conversation_id: UUID, user_id: UUID, message_id: UUID
    ) -> None:
        conversation = await self._require_membership(conversation_id, user_id)
        message = await self._get_message_in_conversation(conversation_id, message_id)
        if message.sender_id != user_id:
            raise MessageDeletePermissionError(
                "Only the sender can delete this message."
            )
        await self._message_repository.delete(message, conversation)
        await self._broadcaster.broadcast(
            conversation_id,
            {
                "event": "message.deleted",
                "message_id": str(message_id),
                "conversation_id": str(conversation_id),
            },
        )

    async def get_attachment(
        self, conversation_id: UUID, user_id: UUID, message_id: UUID
    ) -> Path:
        await self._require_membership(conversation_id, user_id)
        message = await self._get_message_in_conversation(conversation_id, message_id)
        if message.type not in {
            MessageType.image,
            MessageType.file,
            MessageType.video,
        } or message.content is None:
            raise AttachmentNotFoundError("Message does not contain an attachment.")
        path = await self._upload_service.get_attachment_path(message.content)
        if path is None:
            raise AttachmentNotFoundError("Attachment file was not found.")
        return path

    async def get_messages(
        self,
        conversation_id: UUID,
        user_id: UUID,
        last_id: UUID | None,
        limit: int,
    ) -> MessagePageResponse:
        await self._require_membership(conversation_id, user_id)
        last_message = None
        if last_id is not None:
            last_message = await self._message_repository.get_by_id(last_id)
            if (
                last_message is None
                or last_message.conversation_id != conversation_id
            ):
                raise MessageCursorError(
                    "Pagination cursor is not in this conversation."
                )

        messages = await self._message_repository.list_for_conversation(
            conversation_id, last_message, limit
        )
        has_next_page = len(messages) > limit
        page_messages = messages[:limit]
        next_last_id = page_messages[-1].id if has_next_page else None
        return MessagePageResponse(
            messages=[
                MessageResponse.model_validate(message) for message in page_messages
            ],
            next_last_id=next_last_id,
        )

    async def _require_membership(
        self, conversation_id: UUID, user_id: UUID
    ) -> Conversation:
        conversation = await self._conversation_repository.get_by_id(conversation_id)
        if conversation is None:
            raise MessageConversationNotFoundError("Conversation was not found.")
        membership = await self._conversation_repository.get_member(
            conversation_id, user_id
        )
        if membership is None:
            raise MessageAccessError("You are not a member of this conversation.")
        return conversation

    async def _get_message_in_conversation(
        self, conversation_id: UUID, message_id: UUID
    ) -> Message:
        message = await self._message_repository.get_by_id(message_id)
        if message is None or message.conversation_id != conversation_id:
            raise MessageNotFoundError("Message was not found in this conversation.")
        return message

    @staticmethod
    def _normalized_content(content: str) -> str:
        normalized_content = content.strip()
        if not normalized_content:
            raise InvalidMessageContentError("Message content cannot be blank.")
        return normalized_content

    async def _broadcast(self, event: str, message: Message) -> None:
        response = MessageResponse.model_validate(message)
        await self._broadcaster.broadcast(
            message.conversation_id,
            {"event": event, "message": response.model_dump(mode="json")},
        )
