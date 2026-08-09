"""create policy audit events

Revision ID: f13a4b5c6d7e
Revises: e11a1b2c3d4e
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "f13a4b5c6d7e"
down_revision = "e11a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "policy_audit_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "review_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("boundary", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=300), nullable=False),
        sa.Column("resource", sa.String(length=200), nullable=True),
        sa.Column("decision", sa.String(length=30), nullable=False),
        sa.Column("risk", sa.String(length=30), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "matched_rules",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "policy_version",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column(
            "event_metadata",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_policy_audit_events_user_id",
        "policy_audit_events",
        ["user_id"],
    )
    op.create_index(
        "ix_policy_audit_events_conversation_id",
        "policy_audit_events",
        ["conversation_id"],
    )
    op.create_index(
        "ix_policy_audit_events_review_id",
        "policy_audit_events",
        ["review_id"],
    )
    op.create_index(
        "ix_policy_audit_events_decision",
        "policy_audit_events",
        ["decision"],
    )
    op.create_index(
        "ix_policy_audit_events_risk",
        "policy_audit_events",
        ["risk"],
    )
    op.create_index(
        "ix_policy_audit_events_created_at",
        "policy_audit_events",
        ["created_at"],
    )
    op.create_index(
        "ix_policy_audit_user_created",
        "policy_audit_events",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_policy_audit_decision_created",
        "policy_audit_events",
        ["decision", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("policy_audit_events")
