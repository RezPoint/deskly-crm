"""add activity log

Revision ID: 0005_add_activity_log
Revises: 0004_add_users
Create Date: 2026-01-27
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_add_activity_log"
down_revision = "0004_add_users"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "activity_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("entity_type", sa.String(length=30), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("message", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_activity_log_created_at", "activity_log", ["created_at"], unique=False)
    op.create_index("ix_activity_log_user_id", "activity_log", ["user_id"], unique=False)


def downgrade():
    op.drop_index("ix_activity_log_user_id", table_name="activity_log")
    op.drop_index("ix_activity_log_created_at", table_name="activity_log")
    op.drop_table("activity_log")
