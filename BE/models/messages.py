import enum
import uuid
from datetime import datetime
from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from BE.config.database import Base


class MessageType(str, enum.Enum):
    text = "text"
    image = "image"
    file = "file"
    video = "video"
    audio = "audio"
    sticker = "sticker"


class MessageStatus(str, enum.Enum):
    sending = "sending"
    sent = "sent"
    failed = "failed"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reply_to_message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
    )

    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[MessageType] = mapped_column(
        Enum(MessageType, name="message_type"), nullable=False, default=MessageType.text
    )
    status: Mapped[MessageStatus] = mapped_column(
        Enum(MessageStatus, name="message_status"),
        nullable=False,
        default=MessageStatus.sending,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    edited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    conversation = relationship("Conversation", foreign_keys=[conversation_id])
    sender = relationship("User", foreign_keys=[sender_id])
    reply_to = relationship(
        "Message", remote_side=[id], foreign_keys=[reply_to_message_id]
    )
