"""v14 security compliance evidence
Revision ID: v220a1b2c3d4e
Revises: v210a1b2c3d4e
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = "v220a1b2c3d4e"
down_revision = "v210a1b2c3d4e"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("compliance_controls",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("control_id", sa.String(120), nullable=False),
        sa.Column("framework", sa.String(120), nullable=False),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("required_fields", sa.JSON(), nullable=False),
        sa.Column("required_evidence_types", sa.JSON(), nullable=False),
        sa.Column("approval_required", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_compliance_controls_user_id","compliance_controls",["user_id"])
    op.create_index("ix_compliance_control_framework_active","compliance_controls",["framework","active"])
    op.create_index("ix_compliance_control_key_version","compliance_controls",["control_id","version"])

    op.create_table("compliance_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("control_id", sa.String(120), nullable=False),
        sa.Column("evidence_type", sa.String(120), nullable=False),
        sa.Column("source", sa.String(250), nullable=False),
        sa.Column("subject", sa.String(250), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("content_hash", sa.String(128), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_compliance_evidence_user_id","compliance_evidence",["user_id"])
    op.create_index("ix_compliance_evidence_control_created","compliance_evidence",["control_id","created_at"])
    op.create_index("ix_compliance_evidence_subject_created","compliance_evidence",["subject","created_at"])

    op.create_table("compliance_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("control_id", sa.String(120), nullable=False),
        sa.Column("assessment_status", sa.String(20), nullable=False),
        sa.Column("approval_status", sa.String(30), nullable=False),
        sa.Column("assessment", sa.JSON(), nullable=False),
        sa.Column("evidence_snapshot", sa.JSON(), nullable=False),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_compliance_records_user_id","compliance_records",["user_id"])
    op.create_index("ix_compliance_record_control_created","compliance_records",["control_id","created_at"])
    op.create_index("ix_compliance_record_status_created","compliance_records",["assessment_status","created_at"])

def downgrade() -> None:
    op.drop_table("compliance_records")
    op.drop_table("compliance_evidence")
    op.drop_table("compliance_controls")
