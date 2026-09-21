"""Agrega montos auditables de pago en caja.

Revision ID: n5j8k2l4m6p8
Revises: m4h7j9k1n3p5
"""

from alembic import op
import sqlalchemy as sa


revision = "n5j8k2l4m6p8"
down_revision = "m4h7j9k1n3p5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("pagos", sa.Column("received_amount", sa.Numeric(12, 2), nullable=True))
    op.add_column("pagos", sa.Column("change_amount", sa.Numeric(12, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("pagos", "change_amount")
    op.drop_column("pagos", "received_amount")
