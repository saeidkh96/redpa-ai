"""v18.3 control plane run history
Revision ID: v280a1b2c3d4e
Revises: v270a1b2c3d4e
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="v280a1b2c3d4e"; down_revision="v270a1b2c3d4e"; branch_labels=None; depends_on=None
def upgrade():
 op.create_table("agent_execution_runs",sa.Column("id",postgresql.UUID(as_uuid=True),nullable=False),sa.Column("user_id",postgresql.UUID(as_uuid=True),nullable=False),sa.Column("source",sa.String(40),nullable=False),sa.Column("primary_agent",sa.String(120),nullable=False),sa.Column("fallback_agent",sa.String(120)),sa.Column("status",sa.String(30),nullable=False),sa.Column("duration_ms",sa.Float(),nullable=False),sa.Column("evaluation_score",sa.Float()),sa.Column("fallback_count",sa.Integer(),nullable=False),sa.Column("trace_id",sa.String(128)),sa.Column("evidence",sa.JSON(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.PrimaryKeyConstraint("id"))
 op.create_index("ix_agent_execution_runs_user_id","agent_execution_runs",["user_id"]); op.create_index("ix_agent_execution_runs_trace_id","agent_execution_runs",["trace_id"]); op.create_index("ix_agent_execution_status_created","agent_execution_runs",["status","created_at"])
def downgrade(): op.drop_table("agent_execution_runs")
