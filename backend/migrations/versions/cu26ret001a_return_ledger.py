"""Add CU26 return idempotency, beneficiary binding, and RESTOCK movements."""
from alembic import op
import sqlalchemy as sa

revision = "cu26ret001a"
down_revision = "z8v0x2y4a6c8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("devoluciones", sa.Column("beneficiario_id", sa.Integer(), nullable=True))
    op.add_column("devoluciones", sa.Column("idempotency_key", sa.String(length=100), nullable=True))
    op.add_column("devoluciones", sa.Column("request_fingerprint", sa.String(length=64), nullable=True))
    op.create_foreign_key("fk_devoluciones_beneficiario_id", "devoluciones", "usuarios", ["beneficiario_id"], ["id"], ondelete="RESTRICT")
    op.create_index("ix_devoluciones_beneficiario_id", "devoluciones", ["beneficiario_id"])
    op.create_index("ix_devoluciones_idempotency_key", "devoluciones", ["idempotency_key"])
    op.create_unique_constraint("uq_devoluciones_tenant_idempotency_key", "devoluciones", ["tenant_id", "idempotency_key"])
    with op.batch_alter_table("movimientos_inventario") as batch:
        batch.drop_constraint("ck_inventory_movement_type_valid", type_="check")
        batch.create_check_constraint("ck_inventory_movement_type_valid", "movement_type IN ('IN', 'OUT', 'RETURN', 'RESTOCK', 'RESERVE', 'RELEASE', 'SALE')")


def downgrade() -> None:
    with op.batch_alter_table("movimientos_inventario") as batch:
        batch.drop_constraint("ck_inventory_movement_type_valid", type_="check")
        batch.create_check_constraint("ck_inventory_movement_type_valid", "movement_type IN ('IN', 'OUT', 'RETURN', 'RESERVE', 'RELEASE', 'SALE')")
    op.drop_constraint("uq_devoluciones_tenant_idempotency_key", "devoluciones", type_="unique")
    op.drop_index("ix_devoluciones_idempotency_key", table_name="devoluciones")
    op.drop_index("ix_devoluciones_beneficiario_id", table_name="devoluciones")
    op.drop_constraint("fk_devoluciones_beneficiario_id", "devoluciones", type_="foreignkey")
    op.drop_column("devoluciones", "request_fingerprint")
    op.drop_column("devoluciones", "idempotency_key")
    op.drop_column("devoluciones", "beneficiario_id")
