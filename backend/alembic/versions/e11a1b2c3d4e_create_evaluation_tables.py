"""create evaluation tables

Revision ID: e11a1b2c3d4e
Revises: 9b6671617550
Create Date: 2026-08-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e11a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "9b6671617550"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("evaluator_version", sa.String(length=50), nullable=False, server_default=sa.text("'v1'")),
        sa.Column("source_type", sa.String(length=100), nullable=True),
        sa.Column("source_id", sa.String(length=255), nullable=True),
        sa.Column("agent_id", sa.String(length=150), nullable=True),
        sa.Column("model_name", sa.String(length=200), nullable=True),
        sa.Column("aggregate_score", sa.Float(), nullable=True),
        sa.Column("pass_threshold", sa.Float(), nullable=False, server_default=sa.text("0.70")),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('pending','running','completed','failed')", name=op.f("ck_evaluation_runs_status_valid")),
        sa.CheckConstraint("pass_threshold >= 0 AND pass_threshold <= 1", name=op.f("ck_evaluation_runs_pass_threshold_range")),
        sa.CheckConstraint("aggregate_score IS NULL OR (aggregate_score >= 0 AND aggregate_score <= 1)", name=op.f("ck_evaluation_runs_aggregate_score_range")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evaluation_runs")),
    )
    op.create_index(op.f("ix_evaluation_runs_status"), "evaluation_runs", ["status"], unique=False)
    op.create_index(op.f("ix_evaluation_runs_agent_id"), "evaluation_runs", ["agent_id"], unique=False)
    op.create_index("ix_evaluation_runs_status_created_at", "evaluation_runs", ["status", "created_at"], unique=False)
    op.create_index("ix_evaluation_runs_agent_id_created_at", "evaluation_runs", ["agent_id", "created_at"], unique=False)
    op.create_index("ix_evaluation_runs_source_type_source_id", "evaluation_runs", ["source_type", "source_id"], unique=False)

    op.create_table(
        "evaluation_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("run_id", sa.UUID(), nullable=False),
        sa.Column("metric", sa.String(length=100), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, server_default=sa.text("1.0")),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("score >= 0 AND score <= 1", name=op.f("ck_evaluation_results_score_range")),
        sa.CheckConstraint("weight > 0", name=op.f("ck_evaluation_results_weight_positive")),
        sa.ForeignKeyConstraint(["run_id"], ["evaluation_runs.id"], name=op.f("fk_evaluation_results_run_id_evaluation_runs"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evaluation_results")),
    )
    op.create_index(op.f("ix_evaluation_results_run_id"), "evaluation_results", ["run_id"], unique=False)
    op.create_index(op.f("ix_evaluation_results_metric"), "evaluation_results", ["metric"], unique=False)
    op.create_index("ix_evaluation_results_run_id_metric", "evaluation_results", ["run_id", "metric"], unique=True)
    op.create_index("ix_evaluation_results_metric_created_at", "evaluation_results", ["metric", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_evaluation_results_metric_created_at", table_name="evaluation_results")
    op.drop_index("ix_evaluation_results_run_id_metric", table_name="evaluation_results")
    op.drop_index(op.f("ix_evaluation_results_metric"), table_name="evaluation_results")
    op.drop_index(op.f("ix_evaluation_results_run_id"), table_name="evaluation_results")
    op.drop_table("evaluation_results")

    op.drop_index("ix_evaluation_runs_source_type_source_id", table_name="evaluation_runs")
    op.drop_index("ix_evaluation_runs_agent_id_created_at", table_name="evaluation_runs")
    op.drop_index("ix_evaluation_runs_status_created_at", table_name="evaluation_runs")
    op.drop_index(op.f("ix_evaluation_runs_agent_id"), table_name="evaluation_runs")
    op.drop_index(op.f("ix_evaluation_runs_status"), table_name="evaluation_runs")
    op.drop_table("evaluation_runs")
