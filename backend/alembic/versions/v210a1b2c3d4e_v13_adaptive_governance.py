"""v13 adaptive governance

Revision ID: v210a1b2c3d4e
Revises: v200a1b2c3d4e
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "v210a1b2c3d4e"
down_revision = "v200a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "adaptive_governance_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(150), nullable=False),
        sa.Column("agent_id", sa.String(150), nullable=True),
        sa.Column("tenant_id", sa.String(150), nullable=True),
        sa.Column("incident_count", sa.Integer(), nullable=False),
        sa.Column("failure_rate", sa.Float(), nullable=False),
        sa.Column("error_rate", sa.Float(), nullable=False),
        sa.Column("destructive", sa.Boolean(), nullable=False),
        sa.Column("write_access", sa.Boolean(), nullable=False),
        sa.Column("handles_secrets", sa.Boolean(), nullable=False),
        sa.Column("external_network", sa.Boolean(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_adaptive_governance_signals_user_id", "adaptive_governance_signals", ["user_id"])
    op.create_index("ix_adaptive_governance_signal_action_created", "adaptive_governance_signals", ["action", "created_at"])
    op.create_index("ix_adaptive_governance_signal_tenant_created", "adaptive_governance_signals", ["tenant_id", "created_at"])

    op.create_table(
        "adaptive_policy_proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(150), nullable=False),
        sa.Column("recommended_decision", sa.String(20), nullable=False),
        sa.Column("recommended_risk", sa.String(20), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("auto_applied", sa.Boolean(), nullable=False),
        sa.Column("tenant_id", sa.String(150), nullable=True),
        sa.Column("agent_id", sa.String(150), nullable=True),
        sa.Column("source_evidence", sa.JSON(), nullable=False),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("previous_state", sa.JSON(), nullable=False),
        sa.Column("applied_state", sa.JSON(), nullable=False),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rolled_back_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_adaptive_policy_proposals_user_id", "adaptive_policy_proposals", ["user_id"])
    op.create_index("ix_adaptive_policy_action_version", "adaptive_policy_proposals", ["action", "version"])
    op.create_index("ix_adaptive_policy_status_updated", "adaptive_policy_proposals", ["status", "updated_at"])


def downgrade() -> None:
    op.drop_index("ix_adaptive_policy_status_updated", table_name="adaptive_policy_proposals")
    op.drop_index("ix_adaptive_policy_action_version", table_name="adaptive_policy_proposals")
    op.drop_index("ix_adaptive_policy_proposals_user_id", table_name="adaptive_policy_proposals")
    op.drop_table("adaptive_policy_proposals")

    op.drop_index("ix_adaptive_governance_signal_tenant_created", table_name="adaptive_governance_signals")
    op.drop_index("ix_adaptive_governance_signal_action_created", table_name="adaptive_governance_signals")
    op.drop_index("ix_adaptive_governance_signals_user_id", table_name="adaptive_governance_signals")
    op.drop_table("adaptive_governance_signals")
