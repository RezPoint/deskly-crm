"""add invites table

Revision ID: 0010_add_invites
Revises: 0009_add_tenants
Create Date: 2026-01-27
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_add_invites"
down_revision = "0009_add_tenants"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "invites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=200), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False, server_default="viewer"),
        sa.Column("token", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_invites_tenant_id"),
        sa.ForeignKeyConstraint(["accepted_by"], ["users.id"], name="fk_invites_accepted_by"),
        sa.UniqueConstraint("token", name="uq_invites_token"),
    )
    op.create_index("ix_invites_tenant_id", "invites", ["tenant_id"], unique=False)
    op.create_index("ix_invites_token", "invites", ["token"], unique=True)


def downgrade():
    op.drop_index("ix_invites_token", table_name="invites")
    op.drop_index("ix_invites_tenant_id", table_name="invites")
    op.drop_table("invites")
