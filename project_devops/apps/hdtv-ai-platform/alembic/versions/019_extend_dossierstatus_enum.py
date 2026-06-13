"""019: Extend dossierstatus enum with workflow status values.

Revision ID: 019_extend_dossierstatus_enum
Revises: 018_add_alert_title
Create Date: 2026-06-14

Migration 001 created dossierstatus with only: pending, appraising, approved, needs_revision.
The Python entity (DossierStatus) and seed data require additional values:
  draft, submitted_to_dept, dept_approved, dept_rejected,
  submitted_to_board, board_reviewed, rejected

This migration adds all missing values idempotently (checks before ALTER TYPE).
"""

from alembic import op
import sqlalchemy as sa

revision = "019_extend_dossierstatus_enum"
down_revision = "018_add_alert_title"
branch_labels = None
depends_on = None

# Full set of values required by entities.py DossierStatus
REQUIRED_VALUES = [
    "draft",
    "pending",
    "appraising",
    "submitted_to_dept",
    "dept_approved",
    "dept_rejected",
    "submitted_to_board",
    "board_reviewed",
    "approved",
    "rejected",
    "needs_revision",
]


def upgrade() -> None:
    bind = op.get_bind()

    # Get current enum values from PostgreSQL
    existing = {
        row[0]
        for row in bind.execute(
            sa.text(
                "SELECT enumlabel FROM pg_enum e "
                "JOIN pg_type t ON e.enumtypid = t.oid "
                "WHERE t.typname = 'dossierstatus'"
            )
        )
    }

    # Add only missing values — ALTER TYPE ... ADD VALUE is idempotent-safe this way
    for value in REQUIRED_VALUES:
        if value not in existing:
            # Cannot run inside a transaction block for ADD VALUE in PG < 12
            # op.execute with autocommit workaround
            bind.execute(
                sa.text(f"ALTER TYPE dossierstatus ADD VALUE IF NOT EXISTS '{value}'")
            )


def downgrade() -> None:
    # PostgreSQL does not support removing enum values without recreating the type.
    # Downgrade is a no-op — values added are backward compatible.
    pass
