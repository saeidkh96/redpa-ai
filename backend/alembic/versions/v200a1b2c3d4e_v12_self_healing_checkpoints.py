"""v12 self healing checkpoints

Revision ID: v200a1b2c3d4e
Revises: v190a1b2c3d4e
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "v200a1b2c3d4e"
down_revision = "v190a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "self_healing_checkpoints",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "idempotency_key",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "stage",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "failed_agent_id",
            sa.String(length=150),
            nullable=True,
        ),
        sa.Column(
            "replacement_agent_id",
            sa.String(length=150),
            nullable=True,
        ),
        sa.Column(
            "workflow_id",
            sa.String(length=150),
            nullable=True,
        ),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "payload",
            sa.JSON(),
            nullable=False,
        ),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "idempotency_key",
            name="uq_self_healing_checkpoint_idempotency_key",
        ),
    )

    op.create_index(
        "ix_self_healing_checkpoints_idempotency_key",
        "self_healing_checkpoints",
        ["idempotency_key"],
        unique=False,
    )

    op.create_index(
        "ix_self_healing_checkpoint_stage_updated",
        "self_healing_checkpoints",
        ["stage", "updated_at"],
        unique=False,
    )

    op.create_index(
        "ix_self_healing_checkpoint_failed_agent",
        "self_healing_checkpoints",
        ["failed_agent_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_self_healing_checkpoint_failed_agent",
        table_name="self_healing_checkpoints",
    )

    op.drop_index(
        "ix_self_healing_checkpoint_stage_updated",
        table_name="self_healing_checkpoints",
    )

    op.drop_index(
        "ix_self_healing_checkpoints_idempotency_key",
        table_name="self_healing_checkpoints",
    )

    op.drop_table(
        "self_healing_checkpoints"
    )