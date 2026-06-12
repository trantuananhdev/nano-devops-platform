"""015: Add reference_documents table (T-51 — Reference Document Management)

Revision ID: 015_add_reference_documents
Revises: 014_add_audit_logs
Create Date: 2026-06-12

Reference documents for dossiers
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "015_add_reference_documents"
down_revision = "014_add_audit_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    table_exists = bind.execute(
        sa.text("SELECT 1 FROM information_schema.tables WHERE table_name='reference_documents' AND table_schema='public'")
    ).scalar()

    if not table_exists:
        op.create_table(
            "reference_documents",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("dossier_id", sa.Integer(), sa.ForeignKey("dossiers.id"), nullable=False),
            sa.Column("file_name", sa.String(255), nullable=False),
            sa.Column("file_key", sa.String(512), nullable=False),
            sa.Column("file_size", sa.Integer(), nullable=True),
            sa.Column("content_type", sa.String(128), nullable=True),
            sa.Column("uploaded_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column(
                "uploaded_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    idx_exists = lambda name: bind.execute(
        sa.text(f"SELECT 1 FROM pg_indexes WHERE indexname='{name}' AND tablename='reference_documents'")
    ).scalar()
    if not idx_exists("ix_reference_documents_dossier_id"):
        op.create_index("ix_reference_documents_dossier_id", "reference_documents", ["dossier_id"])
    if not idx_exists("ix_reference_documents_uploaded_by"):
        op.create_index("ix_reference_documents_uploaded_by", "reference_documents", ["uploaded_by"])


def downgrade() -> None:
    op.drop_index("ix_reference_documents_uploaded_by", table_name="reference_documents")
    op.drop_index("ix_reference_documents_dossier_id", table_name="reference_documents")
    op.drop_table("reference_documents")
