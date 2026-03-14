"""Add Task model

Revision ID: 79fc3f6fd59a
Revises: 9c2bde372490
Create Date: 2026-03-04 19:07:59.377335

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = '79fc3f6fd59a'
down_revision = '9c2bde372490'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('description', sa.String(length=2000), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='new'),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_id'), 'tasks', ['id'], unique=False)
    op.create_index(op.f('ix_tasks_tenant_id'), 'tasks', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_tasks_order_id'), 'tasks', ['order_id'], unique=False)
    op.create_index(op.f('ix_tasks_due_date'), 'tasks', ['due_date'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tasks_due_date'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_order_id'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_tenant_id'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_id'), table_name='tasks')
    op.drop_table('tasks')
