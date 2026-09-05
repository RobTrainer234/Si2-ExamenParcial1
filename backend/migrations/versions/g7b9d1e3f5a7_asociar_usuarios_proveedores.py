"""Asocia cuentas SUPPLIER con proveedores.

Revision ID: g7b9d1e3f5a7
Revises: f6a8b3c5d7e9
"""

from alembic import op
import sqlalchemy as sa


revision = "g7b9d1e3f5a7"
down_revision = "f6a8b3c5d7e9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("supplier_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_usuarios_supplier_id", "usuarios", "proveedores", ["supplier_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_usuarios_supplier_id", "usuarios", ["supplier_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_usuarios_supplier_id", table_name="usuarios")
    op.drop_constraint("fk_usuarios_supplier_id", "usuarios", type_="foreignkey")
    op.drop_column("usuarios", "supplier_id")
