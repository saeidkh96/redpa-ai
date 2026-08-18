"""v18.1 production hardening evidence

Revision ID: v270a1b2c3d4e
Revises: v260a1b2c3d4e
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "v270a1b2c3d4e"
down_revision = "v260a1b2c3d4e"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "production_hardening_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("release_candidate", sa.String(120), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("report", sa.JSON(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_production_hardening_runs_user_id", "production_hardening_runs", ["user_id"])
    op.create_index("ix_production_hardening_status_created", "production_hardening_runs", ["status", "created_at"])
    op.create_index("ix_production_hardening_release_created", "production_hardening_runs", ["release_candidate", "created_at"])

def downgrade() -> None:
    op.drop_index("ix_production_hardening_release_created", table_name="production_hardening_runs")
    op.drop_index("ix_production_hardening_status_created", table_name="production_hardening_runs")
    op.drop_index("ix_production_hardening_runs_user_id", table_name="production_hardening_runs")
    op.drop_table("production_hardening_runs")
