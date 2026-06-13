"""020: Fix notifications table — rename metadata to extra_data.

Revision ID: 020_fix_notifications_extra_data
Revises: 019_extend_dossierstatus_enum
Create Date: 2026-06-14

Migration 017 created the notifications table with column name 'metadata'.
The Notification entity and seed script use 'extra_data'.
This migration renames the column to match the model.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "020_fix_notifications_extra_data"
down_revision = "019_extend_dossierstatus_enum"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # Check if old column 'metadata' exists
    metadata_exists = bind.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name='notifications' AND column_name='metadata'"
        )
    ).scalar()

    # Check if new column 'extra_data' already exists
    extra_data_exists = bind.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name='notifications' AND column_name='extra_data'"
        )
    ).scalar()

    if metadata_exists and not extra_data_exists:
        # Rename metadata → extra_data
        op.alter_column("notifications", "metadata", new_column_name="extra_data")
    elif not extra_data_exists:
        # Neither column exists — add extra_data fresh
        op.add_column(
            "notifications",
            sa.Column(
                "extra_data",
                postgresql.JSONB(),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    extra_data_exists = bind.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name='notifications' AND column_name='extra_data'"
        )
    ).scalar()
    if extra_data_exists:
        op.alter_column("notifications", "extra_data", new_column_name="metadata")
