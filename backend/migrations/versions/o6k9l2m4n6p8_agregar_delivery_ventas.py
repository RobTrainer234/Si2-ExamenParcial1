"""Agrega fulfillment y snapshot de envio de ventas.

Revision ID: o6k9l2m4n6p8
Revises: n5j8k2l4m6p8
"""

from alembic import op
import sqlalchemy as sa


revision = "o6k9l2m4n6p8"
down_revision = "n5j8k2l4m6p8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ventas", sa.Column("fulfillment_type", sa.String(length=20), nullable=False, server_default="PICKUP"))
    op.create_check_constraint("ck_sales_fulfillment_type", "ventas", "fulfillment_type IN ('PICKUP', 'DELIVERY')")
    op.create_table(
        "envios_venta",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sale_id", sa.Integer(), nullable=False),
        sa.Column("recipient_name", sa.String(length=120), nullable=False),
        sa.Column("recipient_ci", sa.String(length=30), nullable=False),
        sa.Column("recipient_phone", sa.String(length=30), nullable=False),
        sa.Column("department_or_city", sa.String(length=100), nullable=False),
        sa.Column("zone", sa.String(length=120), nullable=False),
        sa.Column("street", sa.String(length=150), nullable=False),
        sa.Column("house_number", sa.String(length=50), nullable=False),
        sa.Column("reference", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["sale_id"], ["ventas.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sale_id", name="uq_envios_venta_sale_id"),
    )
    op.create_index("ix_envios_venta_sale_id", "envios_venta", ["sale_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_envios_venta_sale_id", table_name="envios_venta")
    op.drop_table("envios_venta")
    op.drop_constraint("ck_sales_fulfillment_type", "ventas", type_="check")
    op.drop_column("ventas", "fulfillment_type")
