"""create v8 analytics and connector persistence

Revision ID: v80a1b2c3d4e
Revises: v70a1b2c3d4e
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "v80a1b2c3d4e"
down_revision = "v70a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analytics_fact_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("metric", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1"),
        sa.Column("dimensions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_analytics_fact_metric_time", "analytics_fact_events", ["metric", "occurred_at"])
    op.create_index(
        "ix_analytics_fact_dimensions_gin",
        "analytics_fact_events",
        ["dimensions"],
        postgresql_using="gin",
    )

    op.create_table(
        "enterprise_connectors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("endpoint_url", sa.Text(), nullable=False),
        sa.Column("secret_env_var", sa.String(length=120), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_enterprise_connectors_kind_enabled", "enterprise_connectors", ["kind", "enabled"])

    op.create_table(
        "connector_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "connector_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("enterprise_connectors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("dry_run", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_connector_deliveries_connector_created", "connector_deliveries", ["connector_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_connector_deliveries_connector_created", table_name="connector_deliveries")
    op.drop_table("connector_deliveries")
    op.drop_index("ix_enterprise_connectors_kind_enabled", table_name="enterprise_connectors")
    op.drop_table("enterprise_connectors")
    op.drop_index("ix_analytics_fact_dimensions_gin", table_name="analytics_fact_events")
    op.drop_index("ix_analytics_fact_metric_time", table_name="analytics_fact_events")
    op.drop_table("analytics_fact_events")
