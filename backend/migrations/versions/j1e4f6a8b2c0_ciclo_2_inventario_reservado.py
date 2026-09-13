"""Agrega stock reservado y referencias a movimientos.

Revision ID: j1e4f6a8b2c0
Revises: i9d3f5b7c2e4
"""

from alembic import op
import sqlalchemy as sa


revision = "j1e4f6a8b2c0"
down_revision = "i9d3f5b7c2e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("inventario", sa.Column("reserved_quantity", sa.Integer(), server_default="0", nullable=False))
    op.create_check_constraint("ck_inventory_reserved_valid", "inventario", "reserved_quantity >= 0 AND reserved_quantity <= stock_quantity")
    op.add_column("movimientos_inventario", sa.Column("reference_type", sa.String(length=50), nullable=True))
    op.add_column("movimientos_inventario", sa.Column("reference_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("movimientos_inventario", "reference_id")
    op.drop_column("movimientos_inventario", "reference_type")
    op.drop_constraint("ck_inventory_reserved_valid", "inventario", type_="check")
    op.drop_column("inventario", "reserved_quantity")
