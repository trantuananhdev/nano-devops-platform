"""022: Add llm_token_usage table for per-call token tracking.

Captures actual prompt/completion tokens from Gemini usageMetadata
and llama.cpp OpenAI-compatible usage field.

Revision ID: 022_add_llm_token_usage
Revises: 021_add_user_password_hash
Create Date: 2026-06-13
"""

from alembic import op
import sqlalchemy as sa

revision = "022_add_llm_token_usage"
down_revision = "021_add_user_password_hash"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "llm_token_usage",
        sa.Column("id", sa.Integer, primary_key=True),
        # LLM identity
        sa.Column("role", sa.String(32), nullable=False),        # AgentRole value
        sa.Column("backend", sa.String(16), nullable=False),     # "local" | "gemini"
        sa.Column("model", sa.String(64), nullable=False),       # model name string
        # Token counts (actual from API response, not estimated)
        sa.Column("prompt_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer, nullable=False, server_default="0"),
        # Context (nullable — not every call is tied to a dossier)
        sa.Column("dossier_id", sa.Integer, sa.ForeignKey("dossiers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("session_id", sa.String(64), nullable=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        # Timing
        sa.Column("duration_ms", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    # Query patterns: time range aggregates + per-dossier breakdown
    op.create_index("ix_llm_token_usage_created_at", "llm_token_usage", ["created_at"])
    op.create_index("ix_llm_token_usage_dossier_id", "llm_token_usage", ["dossier_id"])
    op.create_index("ix_llm_token_usage_role_backend", "llm_token_usage", ["role", "backend"])


def downgrade() -> None:
    op.drop_index("ix_llm_token_usage_role_backend", "llm_token_usage")
    op.drop_index("ix_llm_token_usage_dossier_id", "llm_token_usage")
    op.drop_index("ix_llm_token_usage_created_at", "llm_token_usage")
    op.drop_table("llm_token_usage")
