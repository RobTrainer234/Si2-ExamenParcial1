"""Completa backfill del tenant legado, verifica conteos/relaciones y aplica NOT NULL y restricciones finales.

Revision ID: q8m1n4p6r8s0
Revises: p7l0m3n5q7r9
"""

from alembic import op
import sqlalchemy as sa


revision = "q8m1n4p6r8s0"
down_revision = "p7l0m3n5q7r9"
branch_labels = None
depends_on = None

LEGACY_TENANT_NAME = "Empresa Legado"

STRICT_TENANT_NOT_NULL_TABLES: tuple[str, ...] = (
    "sucursales",
    "categorias",
    "proveedores",
    "temporadas",
    "promociones",
    "colecciones",
    "productos",
    "variantes_producto",
    "ofertas_abastecimiento",
    "inventario",
    "reservas",
    "carritos",
    "ventas",
    "pagos",
    "movimientos_inventario",
    "sesiones_vestidor_virtual",
    "recomendaciones_ia",
)

BACKFILL_STATEMENTS: tuple[str, ...] = (
    f"INSERT INTO tenants (name, status) SELECT '{LEGACY_TENANT_NAME}', 'ACTIVE' WHERE NOT EXISTS (SELECT 1 FROM tenants WHERE name = '{LEGACY_TENANT_NAME}')",
    f"UPDATE usuarios SET tenant_id = (SELECT id FROM tenants WHERE name = '{LEGACY_TENANT_NAME}' LIMIT 1) WHERE tenant_id IS NULL",
    f"UPDATE sucursales SET tenant_id = (SELECT id FROM tenants WHERE name = '{LEGACY_TENANT_NAME}' LIMIT 1) WHERE tenant_id IS NULL",
    f"UPDATE categorias SET tenant_id = (SELECT id FROM tenants WHERE name = '{LEGACY_TENANT_NAME}' LIMIT 1) WHERE tenant_id IS NULL",
    f"UPDATE proveedores SET tenant_id = (SELECT id FROM tenants WHERE name = '{LEGACY_TENANT_NAME}' LIMIT 1) WHERE tenant_id IS NULL",
    f"UPDATE temporadas SET tenant_id = (SELECT id FROM tenants WHERE name = '{LEGACY_TENANT_NAME}' LIMIT 1) WHERE tenant_id IS NULL",
    f"UPDATE promociones SET tenant_id = (SELECT id FROM tenants WHERE name = '{LEGACY_TENANT_NAME}' LIMIT 1) WHERE tenant_id IS NULL",
    f"UPDATE colecciones SET tenant_id = COALESCE((SELECT t.tenant_id FROM temporadas t WHERE t.id = colecciones.season_id), (SELECT id FROM tenants WHERE name = '{LEGACY_TENANT_NAME}' LIMIT 1)) WHERE tenant_id IS NULL",
    f"UPDATE productos SET tenant_id = COALESCE((SELECT c.tenant_id FROM categorias c WHERE c.id = productos.category_id), (SELECT id FROM tenants WHERE name = '{LEGACY_TENANT_NAME}' LIMIT 1)) WHERE tenant_id IS NULL",
    f"UPDATE variantes_producto SET tenant_id = COALESCE((SELECT p.tenant_id FROM productos p WHERE p.id = variantes_producto.product_id), (SELECT id FROM tenants WHERE name = '{LEGACY_TENANT_NAME}' LIMIT 1)) WHERE tenant_id IS NULL",
    f"UPDATE ofertas_abastecimiento SET tenant_id = COALESCE((SELECT pr.tenant_id FROM proveedores pr WHERE pr.id = ofertas_abastecimiento.supplier_id), (SELECT id FROM tenants WHERE name = '{LEGACY_TENANT_NAME}' LIMIT 1)) WHERE tenant_id IS NULL",
    f"UPDATE inventario SET tenant_id = COALESCE((SELECT s.tenant_id FROM sucursales s WHERE s.id = inventario.branch_id), (SELECT id FROM tenants WHERE name = '{LEGACY_TENANT_NAME}' LIMIT 1)) WHERE tenant_id IS NULL",
    f"UPDATE reservas SET tenant_id = COALESCE((SELECT s.tenant_id FROM sucursales s WHERE s.id = reservas.branch_id), (SELECT id FROM tenants WHERE name = '{LEGACY_TENANT_NAME}' LIMIT 1)) WHERE tenant_id IS NULL",
    f"UPDATE carritos SET tenant_id = COALESCE((SELECT u.tenant_id FROM usuarios u WHERE u.id = carritos.customer_id), (SELECT id FROM tenants WHERE name = '{LEGACY_TENANT_NAME}' LIMIT 1)) WHERE tenant_id IS NULL",
    f"UPDATE ventas SET tenant_id = COALESCE((SELECT s.tenant_id FROM sucursales s WHERE s.id = ventas.branch_id), (SELECT u.tenant_id FROM usuarios u WHERE u.id = ventas.customer_id), (SELECT id FROM tenants WHERE name = '{LEGACY_TENANT_NAME}' LIMIT 1)) WHERE tenant_id IS NULL",
    f"UPDATE pagos SET tenant_id = COALESCE((SELECT v.tenant_id FROM ventas v WHERE v.id = pagos.sale_id), (SELECT id FROM tenants WHERE name = '{LEGACY_TENANT_NAME}' LIMIT 1)) WHERE tenant_id IS NULL",
    f"UPDATE movimientos_inventario SET tenant_id = COALESCE((SELECT i.tenant_id FROM inventario i WHERE i.id = movimientos_inventario.inventory_id), (SELECT id FROM tenants WHERE name = '{LEGACY_TENANT_NAME}' LIMIT 1)) WHERE tenant_id IS NULL",
    f"UPDATE sesiones_vestidor_virtual SET tenant_id = COALESCE((SELECT p.tenant_id FROM productos p WHERE p.id = sesiones_vestidor_virtual.product_id), (SELECT id FROM tenants WHERE name = '{LEGACY_TENANT_NAME}' LIMIT 1)) WHERE tenant_id IS NULL",
    f"UPDATE recomendaciones_ia SET tenant_id = COALESCE((SELECT p.tenant_id FROM productos p WHERE p.id = recomendaciones_ia.product_id), (SELECT id FROM tenants WHERE name = '{LEGACY_TENANT_NAME}' LIMIT 1)) WHERE tenant_id IS NULL",
    "UPDATE bitacora SET tenant_id = (SELECT u.tenant_id FROM usuarios u WHERE u.id = bitacora.usuario_id) WHERE tenant_id IS NULL AND usuario_id IS NOT NULL",
)

RELATIONSHIP_VERIFICATION_QUERIES: tuple[tuple[str, str], ...] = (
    (
        "colecciones -> temporadas",
        "SELECT COUNT(*) FROM colecciones c JOIN temporadas t ON t.id = c.season_id WHERE c.tenant_id != t.tenant_id",
    ),
    (
        "productos -> categorias",
        "SELECT COUNT(*) FROM productos p JOIN categorias c ON c.id = p.category_id WHERE p.tenant_id != c.tenant_id",
    ),
    (
        "productos -> temporadas",
        "SELECT COUNT(*) FROM productos p JOIN temporadas t ON t.id = p.season_id WHERE p.season_id IS NOT NULL AND p.tenant_id != t.tenant_id",
    ),
    (
        "productos -> colecciones",
        "SELECT COUNT(*) FROM productos p JOIN colecciones c ON c.id = p.collection_id WHERE p.collection_id IS NOT NULL AND p.tenant_id != c.tenant_id",
    ),
    (
        "variantes_producto -> productos",
        "SELECT COUNT(*) FROM variantes_producto v JOIN productos p ON p.id = v.product_id WHERE v.tenant_id != p.tenant_id",
    ),
    (
        "ofertas_abastecimiento -> proveedores/variantes/temporadas",
        "SELECT COUNT(*) FROM ofertas_abastecimiento o "
        "JOIN proveedores pr ON pr.id = o.supplier_id "
        "JOIN variantes_producto v ON v.id = o.product_variant_id "
        "JOIN temporadas t ON t.id = o.season_id "
        "WHERE o.tenant_id != pr.tenant_id OR o.tenant_id != v.tenant_id OR o.tenant_id != t.tenant_id",
    ),
    (
        "inventario -> sucursales/variantes_producto",
        "SELECT COUNT(*) FROM inventario i "
        "JOIN sucursales s ON s.id = i.branch_id "
        "JOIN variantes_producto v ON v.id = i.product_variant_id "
        "WHERE i.tenant_id != s.tenant_id OR i.tenant_id != v.tenant_id",
    ),
    (
        "reservas -> sucursales/usuarios",
        "SELECT COUNT(*) FROM reservas r "
        "JOIN sucursales s ON s.id = r.branch_id "
        "JOIN usuarios u ON u.id = r.customer_id "
        "WHERE r.tenant_id != s.tenant_id OR (u.tenant_id IS NOT NULL AND r.tenant_id != u.tenant_id)",
    ),
    (
        "carritos -> usuarios",
        "SELECT COUNT(*) FROM carritos c JOIN usuarios u ON u.id = c.customer_id WHERE u.tenant_id IS NOT NULL AND c.tenant_id != u.tenant_id",
    ),
    (
        "ventas -> sucursales",
        "SELECT COUNT(*) FROM ventas v JOIN sucursales s ON s.id = v.branch_id WHERE v.branch_id IS NOT NULL AND v.tenant_id != s.tenant_id",
    ),
    (
        "pagos -> ventas",
        "SELECT COUNT(*) FROM pagos p JOIN ventas v ON v.id = p.sale_id WHERE p.tenant_id != v.tenant_id",
    ),
    (
        "movimientos_inventario -> inventario",
        "SELECT COUNT(*) FROM movimientos_inventario m JOIN inventario i ON i.id = m.inventory_id WHERE m.tenant_id != i.tenant_id",
    ),
    (
        "sesiones_vestidor_virtual -> productos",
        "SELECT COUNT(*) FROM sesiones_vestidor_virtual sv JOIN productos p ON p.id = sv.product_id WHERE sv.tenant_id != p.tenant_id",
    ),
    (
        "recomendaciones_ia -> productos",
        "SELECT COUNT(*) FROM recomendaciones_ia r JOIN productos p ON p.id = r.product_id WHERE r.tenant_id != p.tenant_id",
    ),
    (
        "usuario_sucursales -> usuarios/sucursales",
        "SELECT COUNT(*) FROM usuario_sucursales us "
        "JOIN usuarios u ON u.id = us.user_id "
        "JOIN sucursales s ON s.id = us.branch_id "
        "WHERE u.tenant_id IS NOT NULL AND u.tenant_id != s.tenant_id",
    ),
    (
        "producto_proveedores -> productos/proveedores",
        "SELECT COUNT(*) FROM producto_proveedores pp "
        "JOIN productos p ON p.id = pp.product_id "
        "JOIN proveedores pr ON pr.id = pp.supplier_id "
        "WHERE p.tenant_id != pr.tenant_id",
    ),
    (
        "productos_promocion -> promociones/productos",
        "SELECT COUNT(*) FROM productos_promocion pp "
        "JOIN promociones pr ON pr.id = pp.promotion_id "
        "JOIN productos p ON p.id = pp.product_id "
        "WHERE pr.tenant_id != p.tenant_id",
    ),
)

# (table_name, legacy_constraint_name, legacy_columns, new_constraint_name, new_columns, extra_index_name, extra_index_cols)
UNIQUE_CONSTRAINT_MIGRATIONS: tuple[
    tuple[str, str, list[str], str, list[str], str | None, list[str] | None], ...
] = (
    ("usuarios", "uq_users_email", ["email"], "uq_users_tenant_email", ["tenant_id", "email"], "ix_users_email", ["email"]),
    ("sucursales", "uq_branches_city_name", ["city_id", "name"], "uq_branches_tenant_city_name", ["tenant_id", "city_id", "name"], None, None),
    ("categorias", "uq_categories_name", ["name"], "uq_categories_tenant_name", ["tenant_id", "name"], None, None),
    ("proveedores", "uq_suppliers_tax_id", ["tax_id"], "uq_suppliers_tenant_tax_id", ["tenant_id", "tax_id"], None, None),
    ("temporadas", "seasons_name_key", ["name"], "uq_seasons_tenant_name", ["tenant_id", "name"], None, None),
    ("productos", "uq_products_code", ["code"], "uq_products_tenant_code", ["tenant_id", "code"], None, None),
    ("productos", "uq_products_slug", ["slug"], "uq_products_tenant_slug", ["tenant_id", "slug"], None, None),
    ("variantes_producto", "uq_product_variants_sku", ["sku"], "uq_product_variants_tenant_sku", ["tenant_id", "sku"], "ix_product_variants_sku", ["sku"]),
    ("carritos", "carts_customer_id_key", ["customer_id"], "uq_carts_tenant_customer", ["tenant_id", "customer_id"], "ix_carts_customer_id", ["customer_id"]),
    ("pagos", "uq_payment_provider_reference", ["provider", "transaction_reference"], "uq_payments_tenant_provider_reference", ["tenant_id", "provider", "transaction_reference"], None, None),
)


def _verify_counts_and_relationships() -> None:
    ctx = op.get_context()
    if ctx.as_sql:
        return
    bind = op.get_bind()
    for table_name in STRICT_TENANT_NOT_NULL_TABLES:
        null_count = bind.execute(sa.text(f"SELECT COUNT(*) FROM {table_name} WHERE tenant_id IS NULL")).scalar_one()
        if null_count > 0:
            raise RuntimeError(
                f"Verificación T1.1.7 falló: la tabla '{table_name}' conserva {null_count} fila(s) con tenant_id NULL tras el backfill."
            )

    for relation_label, sql_check in RELATIONSHIP_VERIFICATION_QUERIES:
        mismatch_count = bind.execute(sa.text(sql_check)).scalar_one()
        if mismatch_count > 0:
            raise RuntimeError(
                f"Verificación T1.1.7 detectó inconsistencia de relación cross-tenant en '{relation_label}': {mismatch_count} fila(s)."
            )


def upgrade() -> None:
    for statement in BACKFILL_STATEMENTS:
        op.execute(statement)

    _verify_counts_and_relationships()

    for table_name in STRICT_TENANT_NOT_NULL_TABLES:
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.alter_column("tenant_id", existing_type=sa.Integer(), nullable=False)

    for (
        table_name,
        legacy_uq_name,
        _legacy_cols,
        new_uq_name,
        new_cols,
        extra_idx_name,
        extra_idx_cols,
    ) in UNIQUE_CONSTRAINT_MIGRATIONS:
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.drop_constraint(legacy_uq_name, type_="unique")
            batch_op.create_unique_constraint(new_uq_name, new_cols)
            if extra_idx_name and extra_idx_cols:
                batch_op.create_index(extra_idx_name, extra_idx_cols, unique=False)

    # ventas: replace unique index ix_ventas_order_number with uq_sales_tenant_order_number + non-unique ix_sales_order_number
    op.drop_index("ix_ventas_order_number", table_name="ventas")
    with op.batch_alter_table("ventas") as batch_op:
        batch_op.create_unique_constraint("uq_sales_tenant_order_number", ["tenant_id", "order_number"])
        batch_op.create_index("ix_sales_order_number", ["order_number"], unique=False)

    # pagos: replace unique index ix_pagos_idempotency_key with uq_payments_tenant_idempotency_key + non-unique ix_payments_idempotency_key
    op.drop_index("ix_pagos_idempotency_key", table_name="pagos")
    with op.batch_alter_table("pagos") as batch_op:
        batch_op.create_unique_constraint("uq_payments_tenant_idempotency_key", ["tenant_id", "idempotency_key"])
        batch_op.create_index("ix_payments_idempotency_key", ["idempotency_key"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("pagos") as batch_op:
        batch_op.drop_index("ix_payments_idempotency_key")
        batch_op.drop_constraint("uq_payments_tenant_idempotency_key", type_="unique")
    op.create_index("ix_pagos_idempotency_key", "pagos", ["idempotency_key"], unique=True)

    with op.batch_alter_table("ventas") as batch_op:
        batch_op.drop_index("ix_sales_order_number")
        batch_op.drop_constraint("uq_sales_tenant_order_number", type_="unique")
    op.create_index("ix_ventas_order_number", "ventas", ["order_number"], unique=True)

    for (
        table_name,
        legacy_uq_name,
        legacy_cols,
        new_uq_name,
        _new_cols,
        extra_idx_name,
        _extra_idx_cols,
    ) in reversed(UNIQUE_CONSTRAINT_MIGRATIONS):
        with op.batch_alter_table(table_name) as batch_op:
            if extra_idx_name:
                batch_op.drop_index(extra_idx_name)
            batch_op.drop_constraint(new_uq_name, type_="unique")
            batch_op.create_unique_constraint(legacy_uq_name, legacy_cols)

    for table_name in reversed(STRICT_TENANT_NOT_NULL_TABLES):
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.alter_column("tenant_id", existing_type=sa.Integer(), nullable=True)
