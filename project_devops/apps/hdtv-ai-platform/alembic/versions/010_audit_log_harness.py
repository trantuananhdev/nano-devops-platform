"""T-30: Execution Harness — add plan_step_id and error_type to ai_audit_logs.

plan_step_id: correlates audit row → agent_plans.plan_json step ID → OTel trace span
error_type:   records ToolErrorType classification for post-mortem analysis

Revision ID: 010
Revises:     009_agent_clarifications
"""

from alembic import op
import sqlalchemy as sa

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # plan_step_id — nullable String(64), indexed for fast correlation queries
    op.add_column(
        "ai_audit_logs",
        sa.Column(
            "plan_step_id",
            sa.String(64),
            nullable=True,
            comment="Plan step ID from agent_plans.plan_json for audit correlation",
        ),
    )
    op.create_index(
        "ix_ai_audit_logs_plan_step_id",
        "ai_audit_logs",
        ["plan_step_id"],
        unique=False,
    )

    # error_type — nullable String(32) enum-as-string (transient|bad_input|unavailable|unknown)
    op.add_column(
        "ai_audit_logs",
        sa.Column(
            "error_type",
            sa.String(32),
            nullable=True,
            comment="ToolErrorType: transient|bad_input|unavailable|unknown|null (success)",
        ),
    )


def downgrade() -> None:
    op.drop_index("ix_ai_audit_logs_plan_step_id", table_name="ai_audit_logs")
    op.drop_column("ai_audit_logs", "plan_step_id")
    op.drop_column("ai_audit_logs", "error_type")
