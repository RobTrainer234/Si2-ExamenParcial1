"""Refuerza los tipos válidos de movimientos de inventario.

Revision ID: m4h7j9k1n3p5
Revises: l3g6b8c0d2e4
"""

from alembic import op


revision = "m4h7j9k1n3p5"
down_revision = "l3g6b8c0d2e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_inventory_movement_type_valid",
        "movimientos_inventario",
        "movement_type IN ('IN', 'OUT', 'RETURN', 'RESERVE', 'RELEASE', 'SALE')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_inventory_movement_type_valid", "movimientos_inventario", type_="check")
