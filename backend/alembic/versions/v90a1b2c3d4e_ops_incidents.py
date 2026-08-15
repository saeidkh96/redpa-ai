"""create v9 production operations persistence

Revision ID: v90a1b2c3d4e
Revises: v80a1b2c3d4e
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'v90a1b2c3d4e'
down_revision = 'v80a1b2c3d4e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'ops_incidents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('service', sa.String(120), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('status', sa.String(24), nullable=False),
        sa.Column('source', sa.String(80), nullable=False),
        sa.Column('diagnosis', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_ops_incidents_status_created', 'ops_incidents', ['status','created_at'])
    op.create_table(
        'ops_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('ops_incidents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action', sa.String(64), nullable=False),
        sa.Column('target', sa.String(120), nullable=False),
        sa.Column('status', sa.String(24), nullable=False),
        sa.Column('approved', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_ops_actions_incident_created', 'ops_actions', ['incident_id','created_at'])


def downgrade() -> None:
    op.drop_index('ix_ops_actions_incident_created', table_name='ops_actions')
    op.drop_table('ops_actions')
    op.drop_index('ix_ops_incidents_status_created', table_name='ops_incidents')
    op.drop_table('ops_incidents')
