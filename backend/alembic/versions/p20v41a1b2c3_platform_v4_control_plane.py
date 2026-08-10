"""persist v4 model governance, workflow control, and event delivery state

Revision ID: p20v41a1b2c3
Revises: p17a1b2c3d4e
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "p20v41a1b2c3"
down_revision = "p17a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "platform_model_budgets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("period_key", sa.String(length=7), nullable=False),
        sa.Column("monthly_token_limit", sa.Integer(), nullable=False),
        sa.Column("monthly_cost_limit_usd", sa.Float(), nullable=False),
        sa.Column("used_tokens", sa.Integer(), nullable=False),
        sa.Column("used_cost_usd", sa.Float(), nullable=False),
        sa.Column("allowed_providers", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("monthly_token_limit > 0", name="ck_platform_model_budgets_monthly_token_limit_positive"),
        sa.CheckConstraint("monthly_cost_limit_usd > 0", name="ck_platform_model_budgets_monthly_cost_limit_positive"),
        sa.CheckConstraint("used_tokens >= 0", name="ck_platform_model_budgets_used_tokens_non_negative"),
        sa.CheckConstraint("used_cost_usd >= 0", name="ck_platform_model_budgets_used_cost_non_negative"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "period_key", name="uq_platform_model_budget_tenant_period"),
    )
    op.create_index("ix_platform_model_budgets_tenant_id", "platform_model_budgets", ["tenant_id"])
    op.create_index("ix_platform_model_budget_tenant_period", "platform_model_budgets", ["tenant_id", "period_key"])

    op.create_table(
        "platform_model_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_id", sa.String(length=200), nullable=True),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=200), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Float(), nullable=False),
        sa.Column("route_reason", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_platform_model_usage_tenant_id", "platform_model_usage", ["tenant_id"])
    op.create_index("ix_platform_model_usage_request_id", "platform_model_usage", ["request_id"])
    op.create_index("ix_platform_model_usage_created_at", "platform_model_usage", ["created_at"])
    op.create_index("ix_platform_model_usage_tenant_created", "platform_model_usage", ["tenant_id", "created_at"])
    op.create_index("ix_platform_model_usage_provider_created", "platform_model_usage", ["provider", "created_at"])

    op.create_table(
        "platform_workflow_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("version", sa.String(length=40), nullable=False),
        sa.Column("definition", sa.JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "name", "version", name="uq_platform_workflow_definition_version"),
    )
    op.create_index("ix_platform_workflow_definitions_tenant_id", "platform_workflow_definitions", ["tenant_id"])
    op.create_index("ix_platform_workflow_definition_tenant_name", "platform_workflow_definitions", ["tenant_id", "name"])

    op.create_table(
        "platform_workflow_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("definition_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("workflow_name", sa.String(length=160), nullable=False),
        sa.Column("workflow_version", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("current_checkpoint", sa.String(length=200), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("input_payload", sa.JSON(), nullable=False),
        sa.Column("output_payload", sa.JSON(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("correlation_id", sa.String(length=200), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["definition_id"], ["platform_workflow_definitions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_platform_workflow_runs_tenant_id", "platform_workflow_runs", ["tenant_id"])
    op.create_index("ix_platform_workflow_runs_status", "platform_workflow_runs", ["status"])
    op.create_index("ix_platform_workflow_runs_correlation_id", "platform_workflow_runs", ["correlation_id"])
    op.create_index("ix_platform_workflow_run_tenant_status", "platform_workflow_runs", ["tenant_id", "status"])
    op.create_index("ix_platform_workflow_run_definition_created", "platform_workflow_runs", ["definition_id", "created_at"])

    op.create_table(
        "platform_workflow_checkpoints",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("checkpoint_key", sa.String(length=200), nullable=False),
        sa.Column("state", sa.JSON(), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["platform_workflow_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "sequence", name="uq_platform_workflow_checkpoint_sequence"),
    )
    op.create_index("ix_platform_workflow_checkpoints_run_id", "platform_workflow_checkpoints", ["run_id"])
    op.create_index("ix_platform_workflow_checkpoint_run_created", "platform_workflow_checkpoints", ["run_id", "created_at"])

    op.create_table(
        "platform_event_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("consumer", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dead_lettered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replay_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["event_outbox.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "consumer", name="uq_platform_event_delivery_event_consumer"),
    )
    op.create_index("ix_platform_event_deliveries_event_id", "platform_event_deliveries", ["event_id"])
    op.create_index("ix_platform_event_deliveries_tenant_id", "platform_event_deliveries", ["tenant_id"])
    op.create_index("ix_platform_event_deliveries_status", "platform_event_deliveries", ["status"])
    op.create_index("ix_platform_event_delivery_status_retry", "platform_event_deliveries", ["status", "next_retry_at"])
    op.create_index("ix_platform_event_delivery_tenant_status", "platform_event_deliveries", ["tenant_id", "status"])


def downgrade() -> None:
    op.drop_table("platform_event_deliveries")
    op.drop_table("platform_workflow_checkpoints")
    op.drop_table("platform_workflow_runs")
    op.drop_table("platform_workflow_definitions")
    op.drop_table("platform_model_usage")
    op.drop_table("platform_model_budgets")
