"""Agrega ofertas de abastecimiento por variante.

Revision ID: i9d3f5b7c2e4
Revises: h8c2e4f6a1b3
"""

from alembic import op
import sqlalchemy as sa


revision = "i9d3f5b7c2e4"
down_revision = "h8c2e4f6a1b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ofertas_abastecimiento",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("product_variant_id", sa.Integer(), nullable=False),
        sa.Column("season_id", sa.Integer(), nullable=False),
        sa.Column("collection_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="AVAILABLE", nullable=False),
        sa.Column("available_quantity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("expected_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("available_quantity >= 0", name="ck_supply_offer_quantity_nonnegative"),
        sa.CheckConstraint("status IN ('AVAILABLE', 'LIMITED', 'OUT_OF_STOCK', 'UPCOMING')", name="ck_supply_offer_status"),
        sa.ForeignKeyConstraint(["supplier_id"], ["proveedores.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_variant_id"], ["variantes_producto.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["season_id"], ["temporadas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["collection_id"], ["colecciones.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_supply_offer_supplier", "ofertas_abastecimiento", ["supplier_id"])
    op.create_index("ix_supply_offer_variant", "ofertas_abastecimiento", ["product_variant_id"])


def downgrade() -> None:
    op.drop_index("ix_supply_offer_variant", table_name="ofertas_abastecimiento")
    op.drop_index("ix_supply_offer_supplier", table_name="ofertas_abastecimiento")
    op.drop_table("ofertas_abastecimiento")
