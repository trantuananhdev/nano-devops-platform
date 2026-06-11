"""T-16: Add user_preferences table.

Revision ID: 005
Revises: 004
Create Date: 2026-06-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("value", JSONB(), server_default="{}"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_user_preferences_user_id", "user_preferences", ["user_id"])
    # Unique constraint: one value per (user, key)
    op.create_unique_constraint(
        "uq_user_preferences_user_key", "user_preferences", ["user_id", "key"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_user_preferences_user_key", "user_preferences", type_="unique")
    op.drop_index("ix_user_preferences_user_id", table_name="user_preferences")
    op.drop_table("user_preferences")
