"""create event outbox

Revision ID: p17a1b2c3d4e
Revises: p16a1b2c3d4e
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "p17a1b2c3d4e"
down_revision = "p16a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_outbox",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "event_type",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "aggregate_type",
            sa.String(length=120),
            nullable=False,
        ),
        sa.Column(
            "aggregate_id",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "event_metadata",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "correlation_id",
            sa.String(length=200),
            nullable=True,
        ),
        sa.Column(
            "causation_id",
            sa.String(length=200),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "attempts",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_event_outbox_tenant_id",
        "event_outbox",
        ["tenant_id"],
    )
    op.create_index(
        "ix_event_outbox_event_type",
        "event_outbox",
        ["event_type"],
    )
    op.create_index(
        "ix_event_outbox_status",
        "event_outbox",
        ["status"],
    )
    op.create_index(
        "ix_event_outbox_created_at",
        "event_outbox",
        ["created_at"],
    )
    op.create_index(
        "ix_event_outbox_status_created",
        "event_outbox",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_event_outbox_tenant_created",
        "event_outbox",
        ["tenant_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("event_outbox")
