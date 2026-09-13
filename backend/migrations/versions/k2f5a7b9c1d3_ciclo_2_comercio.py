"""Agrega datos de trazabilidad comercial e idempotencia de pagos.

Revision ID: k2f5a7b9c1d3
Revises: j1e4f6a8b2c0
"""

from alembic import op
import sqlalchemy as sa


revision = "k2f5a7b9c1d3"
down_revision = "j1e4f6a8b2c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ventas", sa.Column("order_number", sa.String(length=30), nullable=True))
    op.execute("UPDATE ventas SET order_number = 'LEGACY-' || id WHERE order_number IS NULL")
    op.alter_column("ventas", "order_number", nullable=False)
    op.create_index("ix_ventas_order_number", "ventas", ["order_number"], unique=True)
    op.add_column("ventas", sa.Column("reservation_id", sa.Integer(), nullable=True))
    op.create_index("ix_ventas_reservation_id", "ventas", ["reservation_id"], unique=False)
    op.create_foreign_key("fk_ventas_reservation_id_reservas", "ventas", "reservas", ["reservation_id"], ["id"], ondelete="RESTRICT")
    op.add_column("pagos", sa.Column("idempotency_key", sa.String(length=100), nullable=True))
    op.create_index("ix_pagos_idempotency_key", "pagos", ["idempotency_key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_pagos_idempotency_key", table_name="pagos")
    op.drop_column("pagos", "idempotency_key")
    op.drop_constraint("fk_ventas_reservation_id_reservas", "ventas", type_="foreignkey")
    op.drop_index("ix_ventas_reservation_id", table_name="ventas")
    op.drop_column("ventas", "reservation_id")
    op.drop_index("ix_ventas_order_number", table_name="ventas")
    op.drop_column("ventas", "order_number")
