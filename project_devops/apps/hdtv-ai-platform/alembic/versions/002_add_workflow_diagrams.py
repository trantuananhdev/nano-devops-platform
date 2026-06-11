"""add workflow_diagrams table

Revision ID: 002
Revises: 001
Create Date: 2026-06-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workflow_diagrams",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "dossier_id",
            sa.Integer(),
            sa.ForeignKey("dossiers.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("bpmn_xml", sa.Text(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_workflow_diagrams_dossier_id", "workflow_diagrams", ["dossier_id"])


def downgrade() -> None:
    op.drop_index("ix_workflow_diagrams_dossier_id", table_name="workflow_diagrams")
    op.drop_table("workflow_diagrams")
