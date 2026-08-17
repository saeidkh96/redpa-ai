"""create V10.2 user policy overrides

Revision ID: v102a1b2c3d4e
Revises: v100a1b2c3d4e
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "v102a1b2c3d4e"
down_revision = "v100a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "policy_overrides_v10",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("boundary", sa.String(50), nullable=False),
        sa.Column("action", sa.String(300), nullable=False),
        sa.Column("resource", sa.String(200), nullable=True),
        sa.Column("decision", sa.String(20), nullable=False),
        sa.Column("risk", sa.String(20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "user_id", "boundary", "action",
            name="uq_policy_override_v10_user_boundary_action",
        ),
    )
    op.create_index(
        "ix_policy_overrides_v10_user_enabled",
        "policy_overrides_v10",
        ["user_id", "enabled"],
    )


def downgrade() -> None:
    op.drop_index("ix_policy_overrides_v10_user_enabled", table_name="policy_overrides_v10")
    op.drop_table("policy_overrides_v10")
