"""add last seen timestamp to users

Revision ID: 7c1f3a8d2e4b
Revises: 4f2b7d9c8a1e
Create Date: 2026-09-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7c1f3a8d2e4b"
down_revision: Union[str, Sequence[str], None] = "4f2b7d9c8a1e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "last_seen_at")