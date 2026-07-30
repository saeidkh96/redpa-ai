"""create human reviews table

Revision ID: 9b6671617550
Revises: 5a735c62b6b1
Create Date: 2026-07-30 02:40:19.484408
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# Revision identifiers, used by Alembic.
revision: str = "9b6671617550"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "5a735c62b6b1"

branch_labels: Union[
    str,
    Sequence[str],
    None,
] = None

depends_on: Union[
    str,
    Sequence[str],
    None,
] = None


def upgrade() -> None:
    """Create the human_reviews table."""

    op.create_table(
        "human_reviews",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "message_id",
            sa.UUID(),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column(
            "reason",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "requested_action",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "request_content",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "action_payload",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "reviewer_feedback",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "reviewed_by",
            sa.UUID(),
            nullable=True,
        ),
        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            (
                "status IN ("
                "'pending', "
                "'approved', "
                "'rejected', "
                "'cancelled'"
                ")"
            ),
            name=op.f(
                "ck_human_reviews_status_valid",
            ),
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            name=op.f(
                "fk_human_reviews_conversation_id_conversations",
            ),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["messages.id"],
            name=op.f(
                "fk_human_reviews_message_id_messages",
            ),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"],
            ["users.id"],
            name=op.f(
                "fk_human_reviews_reviewed_by_users",
            ),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f(
                "fk_human_reviews_user_id_users",
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f(
                "pk_human_reviews",
            ),
        ),
    )

    op.create_index(
        op.f(
            "ix_human_reviews_conversation_id",
        ),
        "human_reviews",
        ["conversation_id"],
        unique=False,
    )

    op.create_index(
        "ix_human_reviews_conversation_id_created_at",
        "human_reviews",
        [
            "conversation_id",
            "created_at",
        ],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_human_reviews_message_id",
        ),
        "human_reviews",
        ["message_id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_human_reviews_reviewed_by",
        ),
        "human_reviews",
        ["reviewed_by"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_human_reviews_status",
        ),
        "human_reviews",
        ["status"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_human_reviews_user_id",
        ),
        "human_reviews",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        "ix_human_reviews_user_id_status_created_at",
        "human_reviews",
        [
            "user_id",
            "status",
            "created_at",
        ],
        unique=False,
    )


def downgrade() -> None:
    """Drop the human_reviews table."""

    op.drop_index(
        "ix_human_reviews_user_id_status_created_at",
        table_name="human_reviews",
    )

    op.drop_index(
        op.f(
            "ix_human_reviews_user_id",
        ),
        table_name="human_reviews",
    )

    op.drop_index(
        op.f(
            "ix_human_reviews_status",
        ),
        table_name="human_reviews",
    )

    op.drop_index(
        op.f(
            "ix_human_reviews_reviewed_by",
        ),
        table_name="human_reviews",
    )

    op.drop_index(
        op.f(
            "ix_human_reviews_message_id",
        ),
        table_name="human_reviews",
    )

    op.drop_index(
        "ix_human_reviews_conversation_id_created_at",
        table_name="human_reviews",
    )

    op.drop_index(
        op.f(
            "ix_human_reviews_conversation_id",
        ),
        table_name="human_reviews",
    )

    op.drop_table(
        "human_reviews",
    )