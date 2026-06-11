"""011: Add api_keys table (T-33 — API Key Management)

Revision ID: 011_add_api_keys
Revises: 010_audit_log_harness
Create Date: 2026-06-09

Columns:
  id              SERIAL PRIMARY KEY
  name            VARCHAR(128) NOT NULL
  key_type        ENUM('gemini','mcp','minio','internal') NOT NULL
  key_prefix      VARCHAR(16) NOT NULL   -- first 8 chars, safe to display
  hashed_key      VARCHAR(255) NOT NULL  -- bcrypt hash, never store plaintext
  is_active       BOOLEAN DEFAULT TRUE
  created_by      INT REFERENCES users(id)
  last_used_at    TIMESTAMPTZ
  created_at      TIMESTAMPTZ DEFAULT NOW()
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "011_add_api_keys"
down_revision = "010_audit_log_harness"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM type for key_type
    api_key_type = sa.Enum("gemini", "mcp", "minio", "internal", name="apikeytype")
    api_key_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column(
            "key_type",
            sa.Enum("gemini", "mcp", "minio", "internal", name="apikeytype"),
            nullable=False,
        ),
        sa.Column("key_prefix", sa.String(16), nullable=False),
        sa.Column("hashed_key", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_api_keys_key_type", "api_keys", ["key_type"])
    op.create_index("ix_api_keys_is_active", "api_keys", ["is_active"])


def downgrade() -> None:
    op.drop_index("ix_api_keys_is_active", table_name="api_keys")
    op.drop_index("ix_api_keys_key_type", table_name="api_keys")
    op.drop_table("api_keys")
    sa.Enum(name="apikeytype").drop(op.get_bind(), checkfirst=True)
