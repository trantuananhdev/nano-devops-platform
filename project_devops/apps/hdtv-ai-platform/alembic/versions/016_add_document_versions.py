"""016: Add document_versions table (T-47 — Document Version Control).

Revision ID: 016_add_document_versions
Revises: 015_add_reference_documents
Create Date: 2026-06-12

Version control for dossier documents
"""

from alembic import op
import sqlalchemy as sa

revision = "016_add_document_versions"
down_revision = "015_add_reference_documents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    table_exists = bind.execute(
        sa.text("SELECT 1 FROM information_schema.tables WHERE table_name='document_versions' AND table_schema='public'")
    ).scalar()

    if not table_exists:
        op.create_table(
            "document_versions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("dossier_id", sa.Integer(), sa.ForeignKey("dossiers.id"), nullable=False),
            sa.Column("version_number", sa.Integer(), nullable=False),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column("content_type", sa.String(128), nullable=True),
            sa.Column("change_description", sa.Text(), nullable=True),
            sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    idx_exists = lambda name: bind.execute(
        sa.text(f"SELECT 1 FROM pg_indexes WHERE indexname='{name}' AND tablename='document_versions'")
    ).scalar()
    if not idx_exists("ix_document_versions_dossier_id"):
        op.create_index("ix_document_versions_dossier_id", "document_versions", ["dossier_id"])
    if not idx_exists("ix_document_versions_created_by"):
        op.create_index("ix_document_versions_created_by", "document_versions", ["created_by"])


def downgrade() -> None:
    op.drop_index("ix_document_versions_created_by", table_name="document_versions")
    op.drop_index("ix_document_versions_dossier_id", table_name="document_versions")
    op.drop_table("document_versions")
