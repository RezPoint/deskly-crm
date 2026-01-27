"""add users table

Revision ID: 0004_add_users
Revises: 0003_add_order_search_indexes
Create Date: 2026-01-27
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_add_users"
down_revision = "0003_add_order_search_indexes"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=200), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False, server_default="owner"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)


def downgrade():
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
