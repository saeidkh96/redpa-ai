"""RedPA V16 Agent Evaluation & Continuous Improvement
Revision ID: v240a1b2c3d4e
Revises: v230a1b2c3d4e
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="v240a1b2c3d4e"; down_revision="v230a1b2c3d4e"; branch_labels=None; depends_on=None
def upgrade():
    op.create_table("agent_evaluation_records",
      sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),
      sa.Column("user_id",postgresql.UUID(as_uuid=True),nullable=False),
      sa.Column("subject",sa.String(180),nullable=False),
      sa.Column("status",sa.String(40),nullable=False),
      sa.Column("score",sa.Float(),nullable=False,server_default="0"),
      sa.Column("allowed",sa.Boolean(),nullable=False,server_default=sa.false()),
      sa.Column("payload",sa.JSON(),nullable=False),
      sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_agent_evaluation_records_user", "agent_evaluation_records", ["user_id"])
    op.create_index("ix_agent_evaluation_records_subject", "agent_evaluation_records", ["subject"])
def downgrade(): op.drop_table("agent_evaluation_records")
