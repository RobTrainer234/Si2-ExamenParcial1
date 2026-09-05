"""Traducir nombres de indices al español."""
from alembic import op


revision = "8b3d1e5f7a9c"
down_revision = "7f2a9c1d4e6b"
branch_labels = None
depends_on = None


INDICES = (
    ("ix_users_role_id", "ix_usuarios_role_id"),
    ("ix_refresh_tokens_user_id", "ix_sesiones_actualizacion_user_id"),
    ("ix_branches_city_id", "ix_sucursales_city_id"),
    ("ix_products_category_id", "ix_productos_category_id"),
    ("ix_products_name", "ix_productos_name"),
    ("ix_product_variants_product_id", "ix_variantes_producto_product_id"),
    ("ix_product_images_product_id", "ix_imagenes_producto_product_id"),
    ("ix_inventory_branch_id", "ix_inventario_branch_id"),
    ("ix_inventory_product_variant_id", "ix_inventario_product_variant_id"),
    ("ix_collections_season_id", "ix_colecciones_season_id"),
    ("ix_reservations_branch_id", "ix_reservas_branch_id"),
    ("ix_reservations_customer_id", "ix_reservas_customer_id"),
    ("ix_sales_branch_id", "ix_ventas_branch_id"),
    ("ix_sales_cashier_id", "ix_ventas_cashier_id"),
    ("ix_sales_customer_id", "ix_ventas_customer_id"),
    ("ix_ai_recommendations_customer_id", "ix_recomendaciones_ia_customer_id"),
    ("ix_ai_recommendations_product_id", "ix_recomendaciones_ia_product_id"),
    ("ix_payments_sale_id", "ix_pagos_sale_id"),
    ("ix_cart_items_cart_id", "ix_detalles_carrito_cart_id"),
    ("ix_reservation_items_reservation_id", "ix_detalles_reserva_reservation_id"),
    ("ix_sale_items_sale_id", "ix_detalles_venta_sale_id"),
    ("ix_inventory_movements_created_by", "ix_movimientos_inventario_created_by"),
    ("ix_inventory_movements_inventory_id", "ix_movimientos_inventario_inventory_id"),
    ("ix_virtual_fitting_sessions_customer_id", "ix_sesiones_vestidor_virtual_customer_id"),
    ("ix_virtual_fitting_sessions_product_id", "ix_sesiones_vestidor_virtual_product_id"),
)


def upgrade() -> None:
    for anterior, nuevo in INDICES:
        op.execute(f'ALTER INDEX "{anterior}" RENAME TO "{nuevo}"')


def downgrade() -> None:
    for anterior, nuevo in reversed(INDICES):
        op.execute(f'ALTER INDEX "{nuevo}" RENAME TO "{anterior}"')
