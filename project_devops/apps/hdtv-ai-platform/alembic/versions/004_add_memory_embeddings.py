"""T-15: Add embedding_id column to agent_memories for Chroma vector tracking.

Revision ID: 004
Revises: 003
Create Date: 2026-06-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add embedding_id column (nullable — populated after Chroma upsert)
    op.add_column(
        "agent_memories",
        sa.Column("embedding_id", sa.String(length=128), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("agent_memories", "embedding_id")
