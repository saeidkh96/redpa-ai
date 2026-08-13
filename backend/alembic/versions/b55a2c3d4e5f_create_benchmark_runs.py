"""create benchmark runs table

Revision ID: b55a2c3d4e5f
Revises: p20v41a1b2c3
Create Date: 2026-08-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "b55a2c3d4e5f"
down_revision = "p20v41a1b2c3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "benchmark_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("agent_id", sa.String(length=150), nullable=True),
        sa.Column("model_name", sa.String(length=200), nullable=True),
        sa.Column("aggregate_score", sa.Float(), nullable=False),
        sa.Column("pass_rate", sa.Float(), nullable=False),
        sa.Column("pass_threshold", sa.Float(), nullable=False),
        sa.Column("metric_averages", sa.JSON(), nullable=False),
        sa.Column("case_results", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_benchmark_runs")),
    )
    op.create_index(op.f("ix_benchmark_runs_name"), "benchmark_runs", ["name"], unique=False)
    op.create_index(op.f("ix_benchmark_runs_agent_id"), "benchmark_runs", ["agent_id"], unique=False)
    op.create_index(op.f("ix_benchmark_runs_model_name"), "benchmark_runs", ["model_name"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_benchmark_runs_model_name"), table_name="benchmark_runs")
    op.drop_index(op.f("ix_benchmark_runs_agent_id"), table_name="benchmark_runs")
    op.drop_index(op.f("ix_benchmark_runs_name"), table_name="benchmark_runs")
    op.drop_table("benchmark_runs")
