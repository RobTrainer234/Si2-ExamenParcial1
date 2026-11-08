"""Crear tablas devoluciones y detalles_devolucion para RF17 y CU-26."""
from alembic import op
import sqlalchemy as sa

revision = "z8v0x2y4a6c8"
down_revision = "y7u9w1x3z5b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "devoluciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sucursal_id", sa.Integer(), sa.ForeignKey("sucursales.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("venta_id", sa.Integer(), sa.ForeignKey("ventas.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("cajero_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("autorizado_por", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("numero_devolucion", sa.String(50), nullable=False),
        sa.Column("total_devuelto", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("tipo_reembolso", sa.String(30), nullable=False, server_default="EFECTIVO"),
        sa.Column("codigo_nota_credito", sa.String(50), nullable=True),
        sa.Column("motivo", sa.String(255), nullable=False),
        sa.Column("estado", sa.String(30), nullable=False, server_default="SOLICITADA"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "numero_devolucion", name="uq_devoluciones_tenant_numero"),
        sa.CheckConstraint("total_devuelto >= 0", name="ck_devoluciones_total_nonnegative"),
        sa.CheckConstraint("tipo_reembolso IN ('EFECTIVO', 'NOTA_CREDITO')", name="ck_devoluciones_tipo_reembolso_valid"),
        sa.CheckConstraint("estado IN ('SOLICITADA', 'APROBADA', 'RECHAZADA', 'COMPLETADA')", name="ck_devoluciones_estado_valid"),
    )
    op.create_index("ix_devoluciones_tenant_id", "devoluciones", ["tenant_id"])
    op.create_index("ix_devoluciones_sucursal_id", "devoluciones", ["sucursal_id"])
    op.create_index("ix_devoluciones_venta_id", "devoluciones", ["venta_id"])
    op.create_index("ix_devoluciones_cajero_id", "devoluciones", ["cajero_id"])
    op.create_index("ix_devoluciones_autorizado_por", "devoluciones", ["autorizado_por"])
    op.create_index("ix_devoluciones_tenant_created", "devoluciones", ["tenant_id", "created_at"])

    op.create_table(
        "detalles_devolucion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("devolucion_id", sa.Integer(), sa.ForeignKey("devoluciones.id", ondelete="CASCADE"), nullable=False),
        sa.Column("detalle_venta_id", sa.Integer(), sa.ForeignKey("detalles_venta.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("variante_producto_id", sa.Integer(), sa.ForeignKey("variantes_producto.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("precio_unitario", sa.Numeric(12, 2), nullable=False),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("estado_prenda", sa.String(50), nullable=False, server_default="IMPECABLE"),
        sa.Column("reintegrado_inventario", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.CheckConstraint("cantidad > 0", name="ck_detalles_devolucion_cantidad_positive"),
        sa.CheckConstraint("subtotal >= 0", name="ck_detalles_devolucion_subtotal_nonnegative"),
    )
    op.create_index("ix_detalles_devolucion_devolucion_id", "detalles_devolucion", ["devolucion_id"])
    op.create_index("ix_detalles_devolucion_detalle_venta_id", "detalles_devolucion", ["detalle_venta_id"])
    op.create_index("ix_detalles_devolucion_variante_producto_id", "detalles_devolucion", ["variante_producto_id"])


def downgrade() -> None:
    op.drop_index("ix_detalles_devolucion_variante_producto_id", table_name="detalles_devolucion")
    op.drop_index("ix_detalles_devolucion_detalle_venta_id", table_name="detalles_devolucion")
    op.drop_index("ix_detalles_devolucion_devolucion_id", table_name="detalles_devolucion")
    op.drop_table("detalles_devolucion")

    op.drop_index("ix_devoluciones_tenant_created", table_name="devoluciones")
    op.drop_index("ix_devoluciones_autorizado_por", table_name="devoluciones")
    op.drop_index("ix_devoluciones_cajero_id", table_name="devoluciones")
    op.drop_index("ix_devoluciones_venta_id", table_name="devoluciones")
    op.drop_index("ix_devoluciones_sucursal_id", table_name="devoluciones")
    op.drop_index("ix_devoluciones_tenant_id", table_name="devoluciones")
    op.drop_table("devoluciones")
