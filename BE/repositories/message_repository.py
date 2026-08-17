from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from BE.models.conservations import Conversation
from BE.models.messages import Message, MessageStatus, MessageType


class MessageRepository:
    """Database operations for persisted chat messages."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        conversation: Conversation,
        sender_id: UUID,
        content: str,
        reply_to_message_id: UUID | None = None,
        message_type: MessageType = MessageType.text,
    ) -> Message:
        message = Message(
            conversation_id=conversation.id,
            sender_id=sender_id,
            reply_to_message_id=reply_to_message_id,
            content=content,
            type=message_type,
            status=MessageStatus.sent,
        )
        self._session.add(message)
        await self._session.flush()
        conversation.last_message_id = message.id
        await self._session.commit()
        await self._session.refresh(message)
        return message

    async def get_by_id(self, message_id: UUID) -> Message | None:
        result = await self._session.execute(
            select(Message).where(Message.id == message_id)
        )
        return result.scalar_one_or_none()

    async def list_for_conversation(
        self,
        conversation_id: UUID,
        last_message: Message | None,
        limit: int,
    ) -> list[Message]:
        statement = select(Message).where(Message.conversation_id == conversation_id)
        if last_message is not None:
            statement = statement.where(
                tuple_(Message.created_at, Message.id)
                < tuple_(last_message.created_at, last_message.id)
            )
        statement = statement.order_by(
            Message.created_at.desc(), Message.id.desc()
        ).limit(limit + 1)
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def update_content(
        self, message: Message, content: str, edited_at: datetime
    ) -> Message:
        message.content = content
        message.edited_at = edited_at
        await self._session.commit()
        await self._session.refresh(message)
        return message

    async def count_unread(
        self,
        conversation_id: UUID,
        user_id: UUID,
        last_read_message: Message | None,
    ) -> int:
        statement = select(func.count(Message.id)).where(
            Message.conversation_id == conversation_id,
            Message.sender_id.is_distinct_from(user_id),
        )
        if last_read_message is not None:
            statement = statement.where(
                tuple_(Message.created_at, Message.id)
                > tuple_(last_read_message.created_at, last_read_message.id)
            )
        result = await self._session.execute(statement)
        return result.scalar_one()

    async def delete(self, message: Message, conversation: Conversation) -> None:
        was_last_message = conversation.last_message_id == message.id
        await self._session.delete(message)
        await self._session.flush()
        if was_last_message:
            result = await self._session.execute(
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(Message.created_at.desc(), Message.id.desc())
                .limit(1)
            )
            latest_message = result.scalar_one_or_none()
            conversation.last_message_id = (
                latest_message.id if latest_message is not None else None
            )
        await self._session.commit()
