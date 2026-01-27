"""add payment note

Revision ID: 0011_add_payment_note
Revises: 0010_add_invites
Create Date: 2026-01-27 22:30:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0011_add_payment_note"
down_revision = "0010_add_invites"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("payments", sa.Column("note", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("payments", "note")
