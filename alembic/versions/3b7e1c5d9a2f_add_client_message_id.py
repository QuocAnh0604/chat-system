"""add idempotency key for messages

Revision ID: 3b7e1c5d9a2f
Revises: 2a6d9f4c1b7e
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3b7e1c5d9a2f"
down_revision: Union[str, Sequence[str], None] = "2a6d9f4c1b7e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "messages",
        sa.Column("client_message_id", sa.String(length=100), nullable=True),
    )
    op.create_index(
        "uq_messages_sender_client_message_id",
        "messages",
        ["sender_id", "client_message_id"],
        unique=True,
        postgresql_where=sa.text("client_message_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_messages_sender_client_message_id", table_name="messages"
    )
    op.drop_column("messages", "client_message_id")
