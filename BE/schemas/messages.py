from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from BE.models.messages import MessageStatus, MessageType


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=10_000)


class LazyMessageCreate(MessageCreate):
    target_user_id: UUID


class MessageUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=10_000)


class MessageReadUpdate(BaseModel):
    message_id: UUID


class ReadStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    conversation_id: UUID
    last_read_message_id: UUID | None
    last_read_at: datetime | None


class UnreadCountResponse(BaseModel):
    count: int


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    sender_id: UUID | None
    reply_to_message_id: UUID | None
    content: str | None
    type: MessageType
    status: MessageStatus
    created_at: datetime
    edited_at: datetime | None


class MessagePageResponse(BaseModel):
    messages: list[MessageResponse]
    next_last_id: UUID | None
