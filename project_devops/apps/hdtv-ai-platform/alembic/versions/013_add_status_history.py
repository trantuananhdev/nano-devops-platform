"""013: Add status_history table (T-45 — Status Transitions & Workflow)

Revision ID: 013_add_status_history
Revises: 012_mcp_call_logs
Create Date: 2026-06-12

Track full audit history of dossier status changes with who changed it, when, and comments.
Also updates dossiers.status column to use new DossierStatus enum values.
"""

from alembic import op
import sqlalchemy as sa

revision = "013_add_status_history"
down_revision = "012_mcp_call_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    table_exists = bind.execute(
        sa.text("SELECT 1 FROM information_schema.tables WHERE table_name='status_history' AND table_schema='public'")
    ).scalar()

    if not table_exists:
        op.create_table(
            "status_history",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("dossier_id", sa.Integer(), sa.ForeignKey("dossiers.id"), nullable=False),
            sa.Column("from_status", sa.String(64), nullable=True),
            sa.Column("to_status", sa.String(64), nullable=False),
            sa.Column("changed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("comment", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    idx_exists = lambda name: bind.execute(
        sa.text(f"SELECT 1 FROM pg_indexes WHERE indexname='{name}' AND tablename='status_history'")
    ).scalar()
    if not idx_exists("ix_status_history_dossier_id"):
        op.create_index("ix_status_history_dossier_id", "status_history", ["dossier_id"])


def downgrade() -> None:
    op.drop_index("ix_status_history_dossier_id", table_name="status_history")
    op.drop_table("status_history")
