"""add agentic features: tool_configs, agent_memories, agent_feedbacks, risk_rules, and pdf_text column

Revision ID: 003
Revises: 002
Create Date: 2026-06-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add pdf_text column to dossiers table
    op.add_column("dossiers", sa.Column("pdf_text", sa.Text(), nullable=True))
    
    # Remove unique constraint from workflow_diagrams dossier_id
    op.drop_constraint("workflow_diagrams_dossier_id_key", "workflow_diagrams", type_="unique")
    
    # Create tool_configs table
    op.create_table(
        "tool_configs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("priority", sa.Integer(), server_default="0"),
        sa.Column("config_schema", sa.JSON(), server_default="{}"),
        sa.Column("fallback_response", sa.JSON(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create agent_memories table
    op.create_table(
        "agent_memories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dossier_id", sa.Integer(), sa.ForeignKey("dossiers.id"), nullable=False),
        sa.Column("step", sa.Integer(), nullable=False),
        sa.Column("thought", sa.Text(), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("tool_name", sa.String(length=128), nullable=True),
        sa.Column("tool_input", sa.JSON(), server_default="{}"),
        sa.Column("observation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_agent_memories_dossier_id", "agent_memories", ["dossier_id"])
    
    # Create agent_feedbacks table
    op.create_table(
        "agent_feedbacks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dossier_id", sa.Integer(), sa.ForeignKey("dossiers.id"), nullable=False),
        sa.Column("appraisal_result_id", sa.Integer(), sa.ForeignKey("appraisal_results.id"), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("feedback_type", sa.String(length=64), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("corrected_risk_level", sa.Enum("low", "medium", "high", name="risklevel"), nullable=True),
        sa.Column("metadata", sa.JSON(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_agent_feedbacks_dossier_id", "agent_feedbacks", ["dossier_id"])
    
    # Create risk_rules table
    op.create_table(
        "risk_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("condition_expression", sa.Text(), nullable=False),
        sa.Column("risk_level", sa.Enum("low", "medium", "high", name="risklevel"), nullable=False),
        sa.Column("priority", sa.Integer(), server_default="0"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("risk_rules")
    op.drop_index("ix_agent_feedbacks_dossier_id", table_name="agent_feedbacks")
    op.drop_table("agent_feedbacks")
    op.drop_index("ix_agent_memories_dossier_id", table_name="agent_memories")
    op.drop_table("agent_memories")
    op.drop_table("tool_configs")
    op.create_unique_constraint("workflow_diagrams_dossier_id_key", "workflow_diagrams", ["dossier_id"])
    op.drop_column("dossiers", "pdf_text")
