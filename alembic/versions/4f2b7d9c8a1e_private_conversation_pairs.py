"""add canonical participant pairs for private conversations

Revision ID: 4f2b7d9c8a1e
Revises: ba062e1c33f1
Create Date: 2026-09-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4f2b7d9c8a1e"
down_revision: Union[str, Sequence[str], None] = "ba062e1c33f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversations",
        sa.Column(
            "private_user_id_1",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.add_column(
        "conversations",
        sa.Column(
            "private_user_id_2",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )

    op.execute(
        sa.text(
            """
            UPDATE conversations AS c
            SET private_user_id_1 = participants.user_id_1,
                private_user_id_2 = participants.user_id_2
            FROM (
                SELECT conversation_id,
                       (array_agg(user_id ORDER BY user_id))[1] AS user_id_1,
                       (array_agg(user_id ORDER BY user_id))[2] AS user_id_2
                FROM conversation_members
                GROUP BY conversation_id
                HAVING count(*) = 2
            ) AS participants
            WHERE c.id = participants.conversation_id
              AND c.is_group = false
            """
        )
    )

    op.create_check_constraint(
        "ck_private_conversation_users",
        "conversations",
        "is_group OR (private_user_id_1 IS NOT NULL AND private_user_id_2 IS NOT NULL AND private_user_id_1 < private_user_id_2)",
    )
    op.create_index(
        "uq_private_conversation_users",
        "conversations",
        ["private_user_id_1", "private_user_id_2"],
        unique=True,
        postgresql_where=sa.text("is_group = false"),
    )


def downgrade() -> None:
    op.drop_index("uq_private_conversation_users", table_name="conversations")
    op.drop_constraint(
        "ck_private_conversation_users", "conversations", type_="check"
    )
    op.drop_column("conversations", "private_user_id_2")
    op.drop_column("conversations", "private_user_id_1")
