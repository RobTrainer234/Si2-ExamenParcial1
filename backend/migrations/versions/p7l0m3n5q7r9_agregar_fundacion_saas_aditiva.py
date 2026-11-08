"""Agrega fundacion SaaS aditiva: tablas SaaS, tenant_id nullable, FKs, indices y tenant legado.

Revision ID: p7l0m3n5q7r9
Revises: o6k9l2m4n6p8
"""

from alembic import op
import sqlalchemy as sa


revision = "p7l0m3n5q7r9"
down_revision = "o6k9l2m4n6p8"
branch_labels = None
depends_on = None

LEGACY_TENANT_NAME = "Empresa Legado"

TENANT_TABLES: tuple[tuple[str, str], ...] = (
    ("usuarios", "CASCADE"),
    ("sucursales", "CASCADE"),
    ("categorias", "CASCADE"),
    ("proveedores", "CASCADE"),
    ("temporadas", "CASCADE"),
    ("colecciones", "CASCADE"),
    ("productos", "CASCADE"),
    ("variantes_producto", "CASCADE"),
    ("ofertas_abastecimiento", "CASCADE"),
    ("inventario", "CASCADE"),
    ("reservas", "CASCADE"),
    ("carritos", "CASCADE"),
    ("ventas", "CASCADE"),
    ("pagos", "CASCADE"),
    ("movimientos_inventario", "CASCADE"),
    ("promociones", "CASCADE"),
    ("sesiones_vestidor_virtual", "CASCADE"),
    ("recomendaciones_ia", "CASCADE"),
    ("bitacora", "SET NULL"),
)

COMPOSITE_TENANT_INDEXES: tuple[tuple[str, str, list[str]], ...] = (
    ("ix_products_tenant_category_active", "productos", ["tenant_id", "category_id", "is_active"]),
    ("ix_products_tenant_audience_active", "productos", ["tenant_id", "audience", "is_active"]),
    ("ix_products_tenant_season_active", "productos", ["tenant_id", "season_id", "is_active"]),
    ("ix_products_tenant_collection_active", "productos", ["tenant_id", "collection_id", "is_active"]),
    ("ix_inventory_tenant_branch", "inventario", ["tenant_id", "branch_id"]),
    ("ix_reservations_tenant_status_expires", "reservas", ["tenant_id", "status", "expires_at"]),
    ("ix_sales_tenant_branch_created", "ventas", ["tenant_id", "branch_id", "created_at"]),
    ("ix_bitacora_tenant_created_at", "bitacora", ["tenant_id", "fecha_creacion"]),
)


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "subscription_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("price_monthly", sa.Numeric(precision=12, scale=2), server_default="0.00", nullable=False),
        sa.Column("price_annual", sa.Numeric(precision=12, scale=2), server_default="0.00", nullable=False),
        sa.Column("currency", sa.String(length=10), server_default="BOB", nullable=False),
        sa.Column("max_active_branches", sa.Integer(), nullable=False),
        sa.Column("generative_reports_enabled", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.CheckConstraint("max_active_branches > 0", name="ck_subscription_plans_branch_limit_positive"),
        sa.CheckConstraint("price_monthly >= 0", name="ck_subscription_plans_price_monthly_non_negative"),
        sa.CheckConstraint("price_annual >= 0", name="ck_subscription_plans_price_annual_non_negative"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_subscription_plans_code"),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="ACTIVE", nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'CANCELLED', 'EXPIRED', 'SUSPENDED')",
            name="ck_subscriptions_status_valid",
        ),
        sa.CheckConstraint(
            "valid_until IS NULL OR valid_until > valid_from",
            name="ck_subscriptions_valid_interval",
        ),
        sa.ForeignKeyConstraint(["plan_id"], ["subscription_plans.id"], name="fk_subscriptions_plan_id_subscription_plans", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_subscriptions_tenant_id_tenants", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_subscriptions_tenant_id", "subscriptions", ["tenant_id"], unique=False)
    op.create_index("ix_subscriptions_plan_id", "subscriptions", ["plan_id"], unique=False)

    for table_name, ondelete_rule in TENANT_TABLES:
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.add_column(sa.Column("tenant_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                f"fk_{table_name}_tenant_id_tenants",
                "tenants",
                ["tenant_id"],
                ["id"],
                ondelete=ondelete_rule,
            )
            batch_op.create_index(f"ix_{table_name}_tenant_id", ["tenant_id"], unique=False)

    for index_name, table_name, columns in COMPOSITE_TENANT_INDEXES:
        op.create_index(index_name, table_name, columns, unique=False)

    op.execute(
        f"INSERT INTO tenants (name, status) "
        f"SELECT '{LEGACY_TENANT_NAME}', 'ACTIVE' "
        f"WHERE NOT EXISTS (SELECT 1 FROM tenants WHERE name = '{LEGACY_TENANT_NAME}')"
    )


def downgrade() -> None:
    for index_name, table_name, _ in reversed(COMPOSITE_TENANT_INDEXES):
        op.drop_index(index_name, table_name=table_name)

    for table_name, _ in reversed(TENANT_TABLES):
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.drop_index(f"ix_{table_name}_tenant_id")
            batch_op.drop_constraint(f"fk_{table_name}_tenant_id_tenants", type_="foreignkey")
            batch_op.drop_column("tenant_id")

    op.drop_index("ix_subscriptions_plan_id", table_name="subscriptions")
    op.drop_index("ix_subscriptions_tenant_id", table_name="subscriptions")
    op.drop_table("subscriptions")
    op.drop_table("subscription_plans")
    op.drop_table("tenants")
