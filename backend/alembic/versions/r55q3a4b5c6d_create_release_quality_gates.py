"""create release quality gates

Revision ID: r55q3a4b5c6d
Revises: b55a2c3d4e5f
Create Date: 2026-08-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "r55q3a4b5c6d"
down_revision = "b55a2c3d4e5f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "release_quality_gates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("baseline_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("release_label", sa.String(length=200), nullable=True),
        sa.Column("decision", sa.String(length=16), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("baseline_score", sa.Float(), nullable=False),
        sa.Column("candidate_score", sa.Float(), nullable=False),
        sa.Column("aggregate_delta", sa.Float(), nullable=False),
        sa.Column("regression_detected", sa.Boolean(), nullable=False),
        sa.Column("regressed_metrics", sa.JSON(), nullable=False),
        sa.Column("max_aggregate_drop", sa.Float(), nullable=False),
        sa.Column("max_metric_drop", sa.Float(), nullable=False),
        sa.Column("minimum_candidate_score", sa.Float(), nullable=True),
        sa.Column("require_candidate_pass", sa.Boolean(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["baseline_run_id"], ["evaluation_runs.id"], ondelete="CASCADE", name=op.f("fk_release_quality_gates_baseline_run_id_evaluation_runs")),
        sa.ForeignKeyConstraint(["candidate_run_id"], ["evaluation_runs.id"], ondelete="CASCADE", name=op.f("fk_release_quality_gates_candidate_run_id_evaluation_runs")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_release_quality_gates")),
    )
    op.create_index("ix_release_quality_gates_created_at", "release_quality_gates", ["created_at"], unique=False)
    op.create_index("ix_release_quality_gates_candidate_run_id", "release_quality_gates", ["candidate_run_id"], unique=False)
    op.create_index("ix_release_quality_gates_decision_created_at", "release_quality_gates", ["decision", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_release_quality_gates_decision_created_at", table_name="release_quality_gates")
    op.drop_index("ix_release_quality_gates_candidate_run_id", table_name="release_quality_gates")
    op.drop_index("ix_release_quality_gates_created_at", table_name="release_quality_gates")
    op.drop_table("release_quality_gates")
