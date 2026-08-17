import uuid
import enum
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Enum, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from BE.config.database import Base


class MemberRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class ConversationMember(Base):
    __tablename__ = "conversation_members"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    role: Mapped[MemberRole] = mapped_column(
        Enum(MemberRole, name="member_role"), nullable=False, default=MemberRole.member
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_read_message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", use_alter=True, name="fk_members_last_read_message", ondelete="SET NULL"),
        nullable=True,
    )
    last_read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    conversation = relationship("Conversation", foreign_keys=[conversation_id])
    user = relationship("User", foreign_keys=[user_id])
    last_read_message = relationship("Message", foreign_keys=[last_read_message_id])
