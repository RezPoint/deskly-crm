"""add tenants table

Revision ID: 0009_add_tenants
Revises: 0008_add_tenant_unique_constraints
Create Date: 2026-01-27
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_add_tenants"
down_revision = "0008_add_tenant_unique_constraints"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("slug", name="uq_tenants_slug"),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)

    op.execute("INSERT INTO tenants (id, name, slug) VALUES (1, 'Default', 'default')")

    with op.batch_alter_table("users") as batch:
        batch.create_foreign_key("fk_users_tenant_id", "tenants", ["tenant_id"], ["id"])


def downgrade():
    with op.batch_alter_table("users") as batch:
        batch.drop_constraint("fk_users_tenant_id", type_="foreignkey")

    op.drop_index("ix_tenants_slug", table_name="tenants")
    op.drop_table("tenants")
