"""merge duplicate user last-seen columns

Revision ID: 2a6d9f4c1b7e
Revises: 15e378ea2475
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2a6d9f4c1b7e"
down_revision: Union[str, Sequence[str], None] = "15e378ea2475"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE users SET last_seen_at = COALESCE(last_seen_at, last_seen)"
        )
    )
    op.drop_column("users", "last_seen")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(sa.text("UPDATE users SET last_seen = last_seen_at"))
