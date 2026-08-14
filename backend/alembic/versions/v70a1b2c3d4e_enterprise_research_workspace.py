"""create enterprise research workspace

Revision ID: v70a1b2c3d4e
Revises: q55b4c5d6e7f
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "v70a1b2c3d4e"
down_revision = "q55b4c5d6e7f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "enterprise_research_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("current_stage", sa.String(length=64), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_results", sa.Integer(), nullable=False),
        sa.Column(
            "minimum_quality_score",
            sa.Float(),
            nullable=False,
            server_default="0.65",
        ),
        sa.Column("provider", sa.String(length=64), nullable=True),
        sa.Column("report", sa.Text(), nullable=True),
        sa.Column(
            "evidence",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "quality",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_enterprise_research_runs_status_created",
        "enterprise_research_runs",
        ["status", "created_at"],
    )

    op.create_table(
        "enterprise_research_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "enterprise_research_runs.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column("stage", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_enterprise_research_events_run_created",
        "enterprise_research_events",
        ["run_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_enterprise_research_events_run_created",
        table_name="enterprise_research_events",
    )
    op.drop_table("enterprise_research_events")
    op.drop_index(
        "ix_enterprise_research_runs_status_created",
        table_name="enterprise_research_runs",
    )
    op.drop_table("enterprise_research_runs")
