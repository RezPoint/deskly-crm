"""add tenant id columns

Revision ID: 0007_add_tenant_id
Revises: 0006_add_reminders
Create Date: 2026-01-27
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_add_tenant_id"
down_revision = "0006_add_reminders"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("clients", sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("orders", sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("payments", sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("users", sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("activity_log", sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("reminders", sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="1"))

    op.create_index("ix_clients_tenant_id", "clients", ["tenant_id"])
    op.create_index("ix_orders_tenant_id", "orders", ["tenant_id"])
    op.create_index("ix_payments_tenant_id", "payments", ["tenant_id"])
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_index("ix_activity_log_tenant_id", "activity_log", ["tenant_id"])
    op.create_index("ix_reminders_tenant_id", "reminders", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_reminders_tenant_id", table_name="reminders")
    op.drop_index("ix_activity_log_tenant_id", table_name="activity_log")
    op.drop_index("ix_users_tenant_id", table_name="users")
    op.drop_index("ix_payments_tenant_id", table_name="payments")
    op.drop_index("ix_orders_tenant_id", table_name="orders")
    op.drop_index("ix_clients_tenant_id", table_name="clients")

    op.drop_column("reminders", "tenant_id")
    op.drop_column("activity_log", "tenant_id")
    op.drop_column("users", "tenant_id")
    op.drop_column("payments", "tenant_id")
    op.drop_column("orders", "tenant_id")
    op.drop_column("clients", "tenant_id")
