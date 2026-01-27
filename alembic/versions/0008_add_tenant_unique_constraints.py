"""tenant-scoped unique constraints

Revision ID: 0008_add_tenant_unique_constraints
Revises: 0007_add_tenant_id
Create Date: 2026-01-27
"""

from alembic import op


revision = "0008_add_tenant_unique_constraints"
down_revision = "0007_add_tenant_id"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("clients") as batch:
        batch.drop_constraint("uq_clients_phone", type_="unique")
        batch.drop_constraint("uq_clients_telegram", type_="unique")
        batch.create_unique_constraint("uq_clients_phone_tenant", ["tenant_id", "phone"])
        batch.create_unique_constraint("uq_clients_telegram_tenant", ["tenant_id", "telegram"])

    with op.batch_alter_table("users") as batch:
        batch.drop_constraint("uq_users_email", type_="unique")
        batch.create_unique_constraint("uq_users_email_tenant", ["tenant_id", "email"])


def downgrade():
    with op.batch_alter_table("users") as batch:
        batch.drop_constraint("uq_users_email_tenant", type_="unique")
        batch.create_unique_constraint("uq_users_email", ["email"])

    with op.batch_alter_table("clients") as batch:
        batch.drop_constraint("uq_clients_phone_tenant", type_="unique")
        batch.drop_constraint("uq_clients_telegram_tenant", type_="unique")
        batch.create_unique_constraint("uq_clients_phone", ["phone"])
        batch.create_unique_constraint("uq_clients_telegram", ["telegram"])
