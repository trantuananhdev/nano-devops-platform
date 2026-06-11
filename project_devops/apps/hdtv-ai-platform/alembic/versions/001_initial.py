"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("role", sa.Enum("admin", "hdtv_leader", "dept_head", "specialist", name="userrole"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
    )
    op.create_table(
        "dossiers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("doc_no", sa.String(64), nullable=False, unique=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("unit", sa.String(255), nullable=False),
        sa.Column("risk_level", sa.Enum("high", "medium", "low", name="risklevel"), nullable=False),
        sa.Column("status", sa.Enum("pending", "appraising", "approved", "needs_revision", name="dossierstatus"), nullable=False),
        sa.Column("pdf_url", sa.String(512)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "appraisal_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dossier_id", sa.Integer(), sa.ForeignKey("dossiers.id"), nullable=False),
        sa.Column("overall_risk", sa.Enum("high", "medium", "low", name="risklevel", create_type=False), nullable=False),
        sa.Column("report_md", sa.Text(), server_default=""),
        sa.Column("resolution_md", sa.Text(), server_default=""),
        sa.Column("checks", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dossier_id", sa.Integer(), sa.ForeignKey("dossiers.id")),
        sa.Column("severity", sa.String(32), nullable=False),
        sa.Column("source", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.Enum("open", "resolved", name="alertstatus"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "ai_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_id", sa.String(64), nullable=False, index=True),
        sa.Column("tool_name", sa.String(128), nullable=False),
        sa.Column("execution_time_ms", sa.Integer(), server_default="0"),
        sa.Column("inputs", postgresql.JSONB(), server_default="{}"),
        sa.Column("outputs", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("ai_audit_logs")
    op.drop_table("alerts")
    op.drop_table("appraisal_results")
    op.drop_table("dossiers")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS alertstatus")
    op.execute("DROP TYPE IF EXISTS dossierstatus")
    op.execute("DROP TYPE IF EXISTS risklevel")
    op.execute("DROP TYPE IF EXISTS userrole")
