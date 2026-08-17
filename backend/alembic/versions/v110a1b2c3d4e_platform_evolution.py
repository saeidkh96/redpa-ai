"""V11 autonomous reliability foundation.

Revision ID: v110a1b2c3d4e
Revises: v102a1b2c3d4e
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "v110a1b2c3d4e"
down_revision = "v102a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "platform_evolution_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_platform_evolution_user_version_created",
        "platform_evolution_records",
        ["user_id", "version", "created_at"],
    )
    op.create_index(
        "ix_platform_evolution_kind_created",
        "platform_evolution_records",
        ["kind", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_platform_evolution_kind_created", table_name="platform_evolution_records")
    op.drop_index("ix_platform_evolution_user_version_created", table_name="platform_evolution_records")
    op.drop_table("platform_evolution_records")
