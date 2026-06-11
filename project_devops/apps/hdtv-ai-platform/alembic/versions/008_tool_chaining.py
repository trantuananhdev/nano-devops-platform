"""T-21: Add output_mapping and chains_to JSONB to tool_configs.

Revision ID: 008
Revises: 007
Create Date: 2026-06-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tool_configs",
        sa.Column("output_mapping", JSONB(), nullable=False, server_default="{}"),
    )
    op.add_column(
        "tool_configs",
        sa.Column("chains_to", JSONB(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("tool_configs", "chains_to")
    op.drop_column("tool_configs", "output_mapping")
