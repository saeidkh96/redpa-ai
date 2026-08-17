"""V18 trusted agent registry release checkpoint.

Revision ID: v180a1b2c3d4e
Revises: v170a1b2c3d4e
"""
from alembic import op

revision = "v180a1b2c3d4e"
down_revision = "v170a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Schema-neutral checkpoint. V12-V18 capabilities persist through the
    # V11 platform_evolution_records evidence ledger.
    pass


def downgrade() -> None:
    pass
