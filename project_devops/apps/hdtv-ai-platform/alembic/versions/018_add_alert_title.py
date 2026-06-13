"""018: Add alert title column (T-56).

Revision ID: 018_add_alert_title
Revises: 017_add_notifications
Create Date: 2026-06-13

Adds title field to Alert model
"""

from alembic import op
import sqlalchemy as sa

revision = "018_add_alert_title"
down_revision = "017_add_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    column_exists = bind.execute(
        sa.text("SELECT 1 FROM information_schema.columns WHERE table_name='alerts' AND column_name='title'")
    ).scalar()

    if not column_exists:
        op.add_column("alerts", sa.Column("title", sa.String(length=200), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    column_exists = bind.execute(
        sa.text("SELECT 1 FROM information_schema.columns WHERE table_name='alerts' AND column_name='title'")
    ).scalar()

    if column_exists:
        op.drop_column("alerts", "title")
