"""Add quarantine records for CU-13 exchange returns."""
from alembic import op
import sqlalchemy as sa

revision = "y7u9w1x3z5b7"
down_revision = "x6t8v0z2b4d6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inventory_quarantine",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.Integer(), sa.ForeignKey("sucursales.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("inventory_id", sa.Integer(), sa.ForeignKey("inventario.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("product_variant_id", sa.Integer(), sa.ForeignKey("variantes_producto.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("exchange_item_id", sa.Integer(), sa.ForeignKey("garment_exchange_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("inspected_by", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="SET NULL")),
        sa.Column("inspection_reason", sa.String(255)),
        sa.Column("inspected_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("exchange_item_id", name="uq_inventory_quarantine_exchange_item"),
        sa.CheckConstraint("quantity > 0", name="ck_inventory_quarantine_quantity_positive"),
        sa.CheckConstraint("status IN ('PENDING', 'RELEASED', 'REJECTED')", name="ck_inventory_quarantine_status_valid"),
    )
    op.create_index("ix_inventory_quarantine_tenant_id", "inventory_quarantine", ["tenant_id"])
    op.create_index("ix_inventory_quarantine_branch_id", "inventory_quarantine", ["branch_id"])
    op.create_index("ix_inventory_quarantine_inventory_id", "inventory_quarantine", ["inventory_id"])
    op.create_index("ix_inventory_quarantine_product_variant_id", "inventory_quarantine", ["product_variant_id"])
    op.create_index("ix_inventory_quarantine_exchange_item_id", "inventory_quarantine", ["exchange_item_id"])
    op.create_index("ix_inventory_quarantine_tenant_branch_status", "inventory_quarantine", ["tenant_id", "branch_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_inventory_quarantine_tenant_branch_status", table_name="inventory_quarantine")
    op.drop_index("ix_inventory_quarantine_exchange_item_id", table_name="inventory_quarantine")
    op.drop_index("ix_inventory_quarantine_product_variant_id", table_name="inventory_quarantine")
    op.drop_index("ix_inventory_quarantine_inventory_id", table_name="inventory_quarantine")
    op.drop_index("ix_inventory_quarantine_branch_id", table_name="inventory_quarantine")
    op.drop_index("ix_inventory_quarantine_tenant_id", table_name="inventory_quarantine")
    op.drop_table("inventory_quarantine")
