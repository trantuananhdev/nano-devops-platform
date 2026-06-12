"""014: Add audit_logs table (T-49 — Audit Trail)

Revision ID: 014_add_audit_logs
Revises: 013_add_status_history
Create Date: 2026-06-12

General audit trail for all important actions (create dossier, status change, upload, etc.)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "014_add_audit_logs"
down_revision = "013_add_status_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    table_exists = bind.execute(
        sa.text("SELECT 1 FROM information_schema.tables WHERE table_name='audit_logs' AND table_schema='public'")
    ).scalar()

    if not table_exists:
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("dossier_id", sa.Integer(), sa.ForeignKey("dossiers.id"), nullable=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("action", sa.String(128), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("metadata", JSONB(), nullable=False, server_default="{}"),
            sa.Column("ip_address", sa.String(64), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    idx_exists = lambda name: bind.execute(
        sa.text(f"SELECT 1 FROM pg_indexes WHERE indexname='{name}' AND tablename='audit_logs'")
    ).scalar()
    if not idx_exists("ix_audit_logs_dossier_id"):
        op.create_index("ix_audit_logs_dossier_id", "audit_logs", ["dossier_id"])
    if not idx_exists("ix_audit_logs_user_id"):
        op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    if not idx_exists("ix_audit_logs_action"):
        op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    if not idx_exists("ix_audit_logs_created_at"):
        op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_dossier_id", table_name="audit_logs")
    op.drop_table("audit_logs")
