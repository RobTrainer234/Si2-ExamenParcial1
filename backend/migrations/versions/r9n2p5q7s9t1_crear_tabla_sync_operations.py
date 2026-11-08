"""Crea tabla sync_operations para registrar transacciones offline e idempotencia.

Revision ID: r9n2p5q7s9t1
Revises: q8m1n4p6r8s0
"""

from alembic import op
import sqlalchemy as sa


revision = "r9n2p5q7s9t1"
down_revision = "q8m1n4p6r8s0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sync_operations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("client_operation_id", sa.String(length=64), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("operation_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("conflict_detail", sa.JSON(), nullable=True),
        sa.Column("sale_id", sa.Integer(), nullable=True),
        sa.Column("reservation_id", sa.Integer(), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["sucursales.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sale_id"], ["ventas.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reservation_id"], ["reservas.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("tenant_id", "client_operation_id", name="uq_sync_operations_tenant_client_op_id"),
        sa.CheckConstraint("operation_type IN ('SALE', 'RESERVATION')", name="ck_sync_operations_type"),
        sa.CheckConstraint("status IN ('CONFIRMED', 'CONFLICT', 'REJECTED')", name="ck_sync_operations_status"),
    )
    op.create_index("ix_sync_operations_tenant_id", "sync_operations", ["tenant_id"])
    op.create_index("ix_sync_operations_client_operation_id", "sync_operations", ["client_operation_id"])
    op.create_index("ix_sync_operations_branch_id", "sync_operations", ["branch_id"])
    op.create_index("ix_sync_operations_user_id", "sync_operations", ["user_id"])
    op.create_index("ix_sync_operations_sale_id", "sync_operations", ["sale_id"])
    op.create_index("ix_sync_operations_reservation_id", "sync_operations", ["reservation_id"])
    op.create_index("ix_sync_operations_tenant_created", "sync_operations", ["tenant_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_sync_operations_tenant_created", table_name="sync_operations")
    op.drop_index("ix_sync_operations_reservation_id", table_name="sync_operations")
    op.drop_index("ix_sync_operations_sale_id", table_name="sync_operations")
    op.drop_index("ix_sync_operations_user_id", table_name="sync_operations")
    op.drop_index("ix_sync_operations_branch_id", table_name="sync_operations")
    op.drop_index("ix_sync_operations_client_operation_id", table_name="sync_operations")
    op.drop_index("ix_sync_operations_tenant_id", table_name="sync_operations")
    op.drop_table("sync_operations")
