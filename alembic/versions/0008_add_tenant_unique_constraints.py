"""tenant-scoped unique constraints

Revision ID: 0008_add_tenant_unique_constraints
Revises: 0007_add_tenant_id
Create Date: 2026-01-27
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_add_tenant_unique_constraints"
down_revision = "0007_add_tenant_id"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if bind.dialect.name != "sqlite":
        op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(64)")

    client_uniques = {c["name"] for c in inspector.get_unique_constraints("clients")}
    user_uniques = {c["name"] for c in inspector.get_unique_constraints("users")}

    with op.batch_alter_table("clients") as batch:
        if "uq_clients_phone" in client_uniques:
            batch.drop_constraint("uq_clients_phone", type_="unique")
        if "uq_clients_telegram" in client_uniques:
            batch.drop_constraint("uq_clients_telegram", type_="unique")
        if "uq_clients_phone_tenant" not in client_uniques:
            batch.create_unique_constraint("uq_clients_phone_tenant", ["tenant_id", "phone"])
        if "uq_clients_telegram_tenant" not in client_uniques:
            batch.create_unique_constraint("uq_clients_telegram_tenant", ["tenant_id", "telegram"])

    with op.batch_alter_table("users") as batch:
        if "uq_users_email" in user_uniques:
            batch.drop_constraint("uq_users_email", type_="unique")
        if "uq_users_email_tenant" not in user_uniques:
            batch.create_unique_constraint("uq_users_email_tenant", ["tenant_id", "email"])


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    client_uniques = {c["name"] for c in inspector.get_unique_constraints("clients")}
    user_uniques = {c["name"] for c in inspector.get_unique_constraints("users")}

    with op.batch_alter_table("users") as batch:
        if "uq_users_email_tenant" in user_uniques:
            batch.drop_constraint("uq_users_email_tenant", type_="unique")
        if "uq_users_email" not in user_uniques:
            batch.create_unique_constraint("uq_users_email", ["email"])

    with op.batch_alter_table("clients") as batch:
        if "uq_clients_phone_tenant" in client_uniques:
            batch.drop_constraint("uq_clients_phone_tenant", type_="unique")
        if "uq_clients_telegram_tenant" in client_uniques:
            batch.drop_constraint("uq_clients_telegram_tenant", type_="unique")
        if "uq_clients_phone" not in client_uniques:
            batch.create_unique_constraint("uq_clients_phone", ["phone"])
        if "uq_clients_telegram" not in client_uniques:
            batch.create_unique_constraint("uq_clients_telegram", ["telegram"])
