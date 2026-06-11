"""012: Add mcp_call_logs table (T-36 — MCP Audit Trail)

Revision ID: 012_mcp_call_logs
Revises: 011_add_api_keys
Create Date: 2026-06-09

Per-call audit log for every MCP tool invocation.
Separate from ai_audit_logs to enable dedicated MCP audit views.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "012_mcp_call_logs"
down_revision = "011_add_api_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mcp_call_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("api_key_id", sa.Integer(), sa.ForeignKey("api_keys.id"), nullable=True),
        sa.Column("api_key_prefix", sa.String(16), nullable=False),
        sa.Column("tool_name", sa.String(128), nullable=False),
        sa.Column("inputs", JSONB(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("outputs", JSONB(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("is_error", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_streaming", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("execution_ms", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("output_incomplete", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("missing_fields", JSONB(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mcp_call_logs_api_key_id", "mcp_call_logs", ["api_key_id"])
    op.create_index("ix_mcp_call_logs_tool_name", "mcp_call_logs", ["tool_name"])
    op.create_index("ix_mcp_call_logs_created_at", "mcp_call_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_mcp_call_logs_created_at", table_name="mcp_call_logs")
    op.drop_index("ix_mcp_call_logs_tool_name", table_name="mcp_call_logs")
    op.drop_index("ix_mcp_call_logs_api_key_id", table_name="mcp_call_logs")
    op.drop_table("mcp_call_logs")
