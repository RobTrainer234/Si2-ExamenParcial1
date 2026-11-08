"""Add durable garment exchange ledger and consumed quantities."""
from alembic import op
import sqlalchemy as sa

revision = "x6t8v0z2b4d6"
down_revision = "w5s7u9x1z3b5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "garment_exchanges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True),
        sa.Column("sale_id", sa.Integer(), sa.ForeignKey("ventas.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("branch_id", sa.Integer(), sa.ForeignKey("sucursales.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("idempotency_key", sa.String(100), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="EXCHANGED"),
        sa.Column("returned_value", sa.Numeric(12, 2), nullable=False),
        sa.Column("delivered_value", sa.Numeric(12, 2), nullable=False),
        sa.Column("difference", sa.Numeric(12, 2), nullable=False),
        sa.Column("cash_tendered", sa.Numeric(12, 2)),
        sa.Column("cash_change", sa.Numeric(12, 2)),
        sa.Column("cash_refunded", sa.Numeric(12, 2)),
        sa.Column("cashier_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("result_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_garment_exchanges_tenant_idempotency"),
        sa.CheckConstraint("returned_value >= 0 AND delivered_value >= 0", name="ck_garment_exchange_values_nonnegative"),
    )
    op.create_index("ix_garment_exchanges_tenant_id", "garment_exchanges", ["tenant_id"])
    op.create_index("ix_garment_exchanges_sale_id", "garment_exchanges", ["sale_id"])
    op.create_index("ix_garment_exchanges_branch_id", "garment_exchanges", ["branch_id"])
    op.create_table(
        "garment_exchange_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("exchange_id", sa.Integer(), sa.ForeignKey("garment_exchanges.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sale_item_id", sa.Integer(), sa.ForeignKey("detalles_venta.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("returned_quantity", sa.Integer(), nullable=False),
        sa.Column("new_variant_id", sa.Integer(), sa.ForeignKey("variantes_producto.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("new_quantity", sa.Integer(), nullable=False),
        sa.UniqueConstraint("exchange_id", "sale_item_id", name="uq_garment_exchange_item_sale_item"),
    )
    op.create_index("ix_garment_exchange_items_exchange_id", "garment_exchange_items", ["exchange_id"])
    op.create_index("ix_garment_exchange_items_sale_item_id", "garment_exchange_items", ["sale_item_id"])


def downgrade() -> None:
    op.drop_index("ix_garment_exchange_items_sale_item_id", table_name="garment_exchange_items")
    op.drop_index("ix_garment_exchange_items_exchange_id", table_name="garment_exchange_items")
    op.drop_table("garment_exchange_items")
    op.drop_index("ix_garment_exchanges_branch_id", table_name="garment_exchanges")
    op.drop_index("ix_garment_exchanges_sale_id", table_name="garment_exchanges")
    op.drop_index("ix_garment_exchanges_tenant_id", table_name="garment_exchanges")
    op.drop_table("garment_exchanges")
