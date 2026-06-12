"""017: Add notifications table (T-53 — Notification System).

Revision ID: 017_add_notifications
Revises: 016_add_document_versions
Create Date: 2026-06-12

Notification system for user alerts
"""

from alembic import op
import sqlalchemy as sa

revision = "017_add_notifications"
down_revision = "016_add_document_versions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    table_exists = bind.execute(
        sa.text("SELECT 1 FROM information_schema.tables WHERE table_name='notifications' AND table_schema='public'")
    ).scalar()

    if not table_exists:
        op.create_table(
            "notifications",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("dossier_id", sa.Integer(), sa.ForeignKey("dossiers.id"), nullable=True),
            sa.Column(
                "type",
                sa.Enum(
                    "status_change",
                    "appraisal_complete",
                    "feedback_submitted",
                    "clarification_requested",
                    "document_uploaded",
                    "version_created",
                    name="notificationtype"
                ),
                nullable=False,
            ),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("is_read", sa.Boolean(), server_default=sa.text("false"), nullable=False),
            sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    idx_exists = lambda name: bind.execute(
        sa.text(f"SELECT 1 FROM pg_indexes WHERE indexname='{name}' AND tablename='notifications'")
    ).scalar()
    if not idx_exists("ix_notifications_user_id"):
        op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    if not idx_exists("ix_notifications_dossier_id"):
        op.create_index("ix_notifications_dossier_id", "notifications", ["dossier_id"])
    if not idx_exists("ix_notifications_type"):
        op.create_index("ix_notifications_type", "notifications", ["type"])
    if not idx_exists("ix_notifications_is_read"):
        op.create_index("ix_notifications_is_read", "notifications", ["is_read"])
    if not idx_exists("ix_notifications_created_at"):
        op.create_index("ix_notifications_created_at", "notifications", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_notifications_created_at", table_name="notifications")
    op.drop_index("ix_notifications_is_read", table_name="notifications")
    op.drop_index("ix_notifications_type", table_name="notifications")
    op.drop_index("ix_notifications_dossier_id", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
    op.execute("DROP TYPE IF EXISTS notificationtype")
