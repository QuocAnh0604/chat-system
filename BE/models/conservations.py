import uuid
import enum
from datetime import datetime
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from BE.config.database import Base


class ConversationType(str, enum.Enum):
    private = "private"
    group = "group"


class Conversation(Base):
    __tablename__ = "conversations"

    __table_args__ = (
        CheckConstraint(
            "is_group OR (private_user_id_1 IS NOT NULL AND private_user_id_2 IS NOT NULL AND private_user_id_1 < private_user_id_2)",
            name="ck_private_conversation_users",
        ),
        Index(
            "uq_private_conversation_users",
            "private_user_id_1",
            "private_user_id_2",
            unique=True,
            postgresql_where=text("is_group = false"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    is_group: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    private_user_id_1: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    private_user_id_2: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )

    # nullable vì conversation mới tạo chưa có message nào
    # use_alter=True + post_update=True để phá vòng lặp circular FK với bảng messages
    last_message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", use_alter=True, name="fk_conversations_last_message", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    owner = relationship("User", foreign_keys=[owner_id])
    last_message = relationship(
        "Message", foreign_keys=[last_message_id], post_update=True
    )
