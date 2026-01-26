"""add indexes for filters

Revision ID: 0002_add_indexes
Revises: 0001_init
Create Date: 2026-01-26

"""
from __future__ import annotations

from alembic import op


revision = "0002_add_indexes"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_clients_name", "clients", ["name"])
    op.create_index("ix_orders_client_id", "orders", ["client_id"])
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_index("ix_orders_created_at", "orders", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_orders_created_at", table_name="orders")
    op.drop_index("ix_orders_status", table_name="orders")
    op.drop_index("ix_orders_client_id", table_name="orders")
    op.drop_index("ix_clients_name", table_name="clients")
