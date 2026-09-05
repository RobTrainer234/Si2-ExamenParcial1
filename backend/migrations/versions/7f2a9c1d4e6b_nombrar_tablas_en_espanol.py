"""Traducir nombres físicos de tablas al español.

Revision ID: 7f2a9c1d4e6b
Revises: 5c6e7f44ee6b
"""
from alembic import op


revision = "7f2a9c1d4e6b"
down_revision = "5c6e7f44ee6b"
branch_labels = None
depends_on = None


TABLAS = (
    ("users", "usuarios"),
    ("refresh_tokens", "sesiones_actualizacion"),
    ("cities", "ciudades"),
    ("branches", "sucursales"),
    ("categories", "categorias"),
    ("sizes", "tallas"),
    ("colors", "colores"),
    ("suppliers", "proveedores"),
    ("products", "productos"),
    ("product_suppliers", "producto_proveedores"),
    ("product_variants", "variantes_producto"),
    ("product_images", "imagenes_producto"),
    ("inventory", "inventario"),
    ("seasons", "temporadas"),
    ("collections", "colecciones"),
    ("reservations", "reservas"),
    ("reservation_items", "detalles_reserva"),
    ("carts", "carritos"),
    ("cart_items", "detalles_carrito"),
    ("sales", "ventas"),
    ("sale_items", "detalles_venta"),
    ("payments", "pagos"),
    ("inventory_movements", "movimientos_inventario"),
    ("promotions", "promociones"),
    ("promotion_products", "productos_promocion"),
    ("virtual_fitting_sessions", "sesiones_vestidor_virtual"),
    ("ai_recommendations", "recomendaciones_ia"),
)


def upgrade() -> None:
    for anterior, nuevo in TABLAS:
        op.rename_table(anterior, nuevo)


def downgrade() -> None:
    for anterior, nuevo in reversed(TABLAS):
        op.rename_table(nuevo, anterior)
