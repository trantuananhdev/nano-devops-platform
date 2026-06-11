"""T-19: Add critic_verdict JSONB to appraisal_results.

Revision ID: 007
Revises: 006
Create Date: 2026-06-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "appraisal_results",
        sa.Column("critic_verdict", JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("appraisal_results", "critic_verdict")
