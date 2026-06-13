"""021: Add password_hash to users table for JWT auth.

Revision ID: 021_add_user_password_hash
Revises: 020_fix_notifications_extra_data
Create Date: 2026-06-13
"""

from alembic import op
import sqlalchemy as sa

revision = "021_add_user_password_hash"
down_revision = "020_fix_notifications_extra_data"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    col_exists = bind.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name='users' AND column_name='password_hash'"
        )
    ).scalar()
    if not col_exists:
        op.add_column(
            "users",
            sa.Column("password_hash", sa.String(255), nullable=True),
        )


def downgrade() -> None:
    op.drop_column("users", "password_hash")
