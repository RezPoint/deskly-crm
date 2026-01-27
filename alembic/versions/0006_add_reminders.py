"""add reminders

Revision ID: 0006_add_reminders
Revises: 0005_add_activity_log
Create Date: 2026-01-27
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_add_reminders"
down_revision = "0005_add_activity_log"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "reminders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("entity_type", sa.String(length=30), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_reminders_due_at", "reminders", ["due_at"], unique=False)


def downgrade():
    op.drop_index("ix_reminders_due_at", table_name="reminders")
    op.drop_table("reminders")
