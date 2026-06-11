"""T-22: Add agent_clarifications table for human-in-the-loop pauses.

Revision ID: 009
Revises: 008
Create Date: 2026-06-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_clarifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dossier_id", sa.Integer(), sa.ForeignKey("dossiers.id"), nullable=False, index=True),
        sa.Column("task_id", sa.String(64), nullable=False, index=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("options", JSONB(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("answer", sa.String(512), nullable=True),
        sa.Column("trigger_type", sa.String(64), nullable=True),
        sa.Column("resume_state", JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("agent_clarifications")
