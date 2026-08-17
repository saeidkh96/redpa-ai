"""v11 ops production validation hardening

Revision ID: v190a1b2c3d4e
Revises: v180a1b2c3d4e
"""
from alembic import op
import sqlalchemy as sa

revision = "v190a1b2c3d4e"
down_revision = "v180a1b2c3d4e"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("ops_actions", sa.Column("idempotency_key", sa.String(200), nullable=True))
    op.create_unique_constraint(
        "uq_ops_actions_incident_idempotency",
        "ops_actions",
        ["incident_id", "idempotency_key"],
    )

def downgrade() -> None:
    op.drop_constraint("uq_ops_actions_incident_idempotency", "ops_actions", type_="unique")
    op.drop_column("ops_actions", "idempotency_key")
