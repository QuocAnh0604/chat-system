"""init schema

Revision ID: ba062e1c33f1
Revises: 
Create Date: 2026-08-13 23:51:52.016245

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba062e1c33f1'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # 1. Users
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=True,
    )

    op.create_index(
        "ix_users_username",
        "users",
        ["username"],
        unique=True,
    )

    # 2. Conversations
    # NOTE:
    # last_message_id -> messages.id is added later
    # because messages table does not exist yet.
    op.create_table(
        "conversations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("is_group", sa.Boolean(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=True),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("owner_id", sa.UUID(), nullable=True),
        sa.Column("last_message_id", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 3. Refresh tokens
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_refresh_tokens_user_id",
        "refresh_tokens",
        ["user_id"],
    )

    # 4. Messages
    op.create_table(
        "messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=False),
        sa.Column("sender_id", sa.UUID(), nullable=True),
        sa.Column("reply_to_message_id", sa.UUID(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column(
            "type",
            sa.Enum(
                "text",
                "image",
                "file",
                "video",
                "audio",
                "sticker",
                name="message_type",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "sending",
                "sent",
                "failed",
                name="message_status",
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "edited_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reply_to_message_id"],
            ["messages.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["sender_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Better index for:
    # WHERE conversation_id = ?
    # ORDER BY created_at DESC
    # LIMIT ...
    op.create_index(
        "ix_messages_conversation_created_at",
        "messages",
        ["conversation_id", "created_at"],
    )

    # 5. Conversation members
    # NOTE:
    # last_read_message_id -> messages.id is added later.
    op.create_table(
        "conversation_members",
        sa.Column("conversation_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "owner",
                "admin",
                "member",
                name="member_role",
            ),
            nullable=False,
        ),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_read_message_id",
            sa.UUID(),
            nullable=True,
        ),
        sa.Column(
            "last_read_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "conversation_id",
            "user_id",
        ),
    )

    # 6. Add circular foreign keys after all tables exist
    op.create_foreign_key(
        "fk_conversations_last_message",
        "conversations",
        "messages",
        ["last_message_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_foreign_key(
        "fk_members_last_read_message",
        "conversation_members",
        "messages",
        ["last_read_message_id"],
        ["id"],
        ondelete="SET NULL",
    )

def downgrade() -> None:
    """Downgrade schema."""

    # Remove circular foreign keys first
    op.drop_constraint(
        "fk_members_last_read_message",
        "conversation_members",
        type_="foreignkey",
    )

    op.drop_constraint(
        "fk_conversations_last_message",
        "conversations",
        type_="foreignkey",
    )

    # Drop tables in reverse dependency order
    op.drop_table("conversation_members")

    op.drop_index(
        "ix_messages_conversation_created_at",
        table_name="messages",
    )
    op.drop_table("messages")

    op.drop_index(
        "ix_refresh_tokens_user_id",
        table_name="refresh_tokens",
    )
    op.drop_table("refresh_tokens")

    op.drop_table("conversations")

    op.drop_index(
        "ix_users_username",
        table_name="users",
    )
    op.drop_index(
        "ix_users_email",
        table_name="users",
    )
    op.drop_table("users")