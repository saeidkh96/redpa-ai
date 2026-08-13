"""create benchmark suites and reliability snapshots

Revision ID: q55b4c5d6e7f
Revises: r55q3a4b5c6d
Create Date: 2026-08-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "q55b4c5d6e7f"
down_revision = "r55q3a4b5c6d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "benchmark_suites",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cases", sa.JSON(), nullable=False),
        sa.Column("pass_threshold", sa.Float(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_benchmark_suites")),
    )
    op.create_index("ix_benchmark_suites_name", "benchmark_suites", ["name"], unique=False)
    op.create_index("ix_benchmark_suites_enabled", "benchmark_suites", ["enabled"], unique=False)

    op.create_table(
        "reliability_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("healthy_providers", sa.Integer(), nullable=False),
        sa.Column("degraded_providers", sa.Integer(), nullable=False),
        sa.Column("unavailable_providers", sa.Integer(), nullable=False),
        sa.Column("providers", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reliability_snapshots")),
    )
    op.create_index("ix_reliability_snapshots_created_at", "reliability_snapshots", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_reliability_snapshots_created_at", table_name="reliability_snapshots")
    op.drop_table("reliability_snapshots")
    op.drop_index("ix_benchmark_suites_enabled", table_name="benchmark_suites")
    op.drop_index("ix_benchmark_suites_name", table_name="benchmark_suites")
    op.drop_table("benchmark_suites")
