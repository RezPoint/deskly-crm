"""add order search indexes

Revision ID: 0003_add_order_search_indexes
Revises: 0002_add_indexes
Create Date: 2026-01-26

"""
from __future__ import annotations

from alembic import op


revision = "0003_add_order_search_indexes"
down_revision = "0002_add_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_orders_title", "orders", ["title"])
    op.create_index("ix_orders_comment", "orders", ["comment"])


def downgrade() -> None:
    op.drop_index("ix_orders_comment", table_name="orders")
    op.drop_index("ix_orders_title", table_name="orders")
