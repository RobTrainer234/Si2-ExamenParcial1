from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import JSON, Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric, PrimaryKeyConstraint, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", server_default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    users: Mapped[list["User"]] = relationship(back_populates="tenant")
    branches: Mapped[list["Branch"]] = relationship(back_populates="tenant")
    categories: Mapped[list["Category"]] = relationship(back_populates="tenant")
    suppliers: Mapped[list["Supplier"]] = relationship(back_populates="tenant")
    seasons: Mapped[list["Season"]] = relationship(back_populates="tenant")
    collections: Mapped[list["Collection"]] = relationship(back_populates="tenant")
    products: Mapped[list["Product"]] = relationship(back_populates="tenant")
    product_variants: Mapped[list["ProductVariant"]] = relationship(back_populates="tenant")
    inventories: Mapped[list["Inventory"]] = relationship(back_populates="tenant")
    reservations: Mapped[list["Reservation"]] = relationship(back_populates="tenant")
    carts: Mapped[list["Cart"]] = relationship(back_populates="tenant")
    sales: Mapped[list["Sale"]] = relationship(back_populates="tenant")
    payments: Mapped[list["Payment"]] = relationship(back_populates="tenant")
    inventory_movements: Mapped[list["InventoryMovement"]] = relationship(back_populates="tenant")
    promotions: Mapped[list["Promotion"]] = relationship(back_populates="tenant")
    supply_offers: Mapped[list["SupplierSupplyOffer"]] = relationship(back_populates="tenant")
    virtual_fitting_sessions: Mapped[list["VirtualFittingSession"]] = relationship(back_populates="tenant")
    ai_recommendations: Mapped[list["AIRecommendation"]] = relationship(back_populates="tenant")
    bitacoras: Mapped[list["Bitacora"]] = relationship(back_populates="tenant")
    sync_operations: Mapped[list["SyncOperation"]] = relationship(back_populates="tenant")
    garment_exchanges: Mapped[list["GarmentExchange"]] = relationship(back_populates="tenant")
    quarantine_records: Mapped[list["InventoryQuarantine"]] = relationship(back_populates="tenant")
    credit_note_redemptions: Mapped[list["CreditNoteRedemption"]] = relationship(back_populates="tenant")


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    __table_args__ = (
        UniqueConstraint("code", name="uq_subscription_plans_code"),
        CheckConstraint("max_active_branches > 0", name="ck_subscription_plans_branch_limit_positive"),
        CheckConstraint("price_monthly >= 0", name="ck_subscription_plans_price_monthly_non_negative"),
        CheckConstraint("price_annual >= 0", name="ck_subscription_plans_price_annual_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price_monthly: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default="0.00")
    price_annual: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default="0.00")
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="BOB", server_default="BOB")
    max_active_branches: Mapped[int] = mapped_column(Integer, nullable=False)
    generative_reports_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="plan")


class PendingPaidSignup(Base):
    __tablename__ = "pending_paid_signups"
    __table_args__ = (
        UniqueConstraint("stripe_session_id", name="uq_pending_paid_signups_stripe_session_id"),
        Index("ix_pending_paid_signups_email_status", "email", "status"),
        Index(
            "uq_pending_paid_signups_in_flight_email",
            "email",
            unique=True,
            sqlite_where=text("status IN ('PENDING', 'CHECKOUT_CREATED')"),
            postgresql_where=text("status IN ('PENDING', 'CHECKOUT_CREATED')"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company_name: Mapped[str] = mapped_column(String(150), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    plan_id: Mapped[int] = mapped_column(ForeignKey("subscription_plans.id", ondelete="RESTRICT"), nullable=False, index=True)
    billing_interval: Mapped[str] = mapped_column(String(10), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING", server_default="PENDING")
    stripe_session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_session_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    stripe_idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    request_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    checkout_capability_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    capability_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    plan: Mapped["SubscriptionPlan"] = relationship()


class EmailVerificationChallenge(Base):
    __tablename__ = "email_verification_challenges"
    __table_args__ = (UniqueConstraint("email", name="uq_email_verification_email"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    send_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    window_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    capability_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    capability_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    capability_bound_pending_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class EmailOutbox(Base):
    __tablename__ = "email_outbox"
    __table_args__ = (UniqueConstraint("dedupe_key", name="uq_email_outbox_dedupe_key"), Index("ix_email_outbox_status_next_attempt", "status", "next_attempt_at"))

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(80), nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    html_body: Mapped[str] = mapped_column(Text, nullable=False)
    text_body: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", server_default="PENDING")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    leased_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(String(500))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE', 'CANCELLED', 'EXPIRED', 'SUSPENDED', 'PAUSED')", name="ck_subscriptions_status_valid"),
        CheckConstraint("valid_until IS NULL OR valid_until > valid_from", name="ck_subscriptions_valid_interval"),
        UniqueConstraint("provider_subscription_id", name="uq_subscriptions_provider_subscription_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("subscription_plans.id", ondelete="RESTRICT"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", server_default="ACTIVE")
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    provider_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    provider_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    billing_interval: Mapped[str | None] = mapped_column(String(10), nullable=True)
    provider_event_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    tenant: Mapped[Tenant] = relationship(back_populates="subscriptions")
    plan: Mapped[SubscriptionPlan] = relationship(back_populates="subscriptions")


class ProcessedStripeEvent(Base):
    __tablename__ = "processed_stripe_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="role")
    permissions: Mapped[list["Permission"]] = relationship(secondary="rol_permisos", back_populates="roles")


class Permission(Base):
    __tablename__ = "permisos"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    roles: Mapped[list[Role]] = relationship(secondary="rol_permisos", back_populates="permissions")


class RolePermission(Base):
    __tablename__ = "rol_permisos"
    __table_args__ = (PrimaryKeyConstraint("role_id", "permission_id"),)

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"))
    permission_id: Mapped[int] = mapped_column(ForeignKey("permisos.id", ondelete="CASCADE"))


class User(Base):
    __tablename__ = "usuarios"
    __table_args__ = (UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False, index=True)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("proveedores.id", ondelete="SET NULL"), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    tenant: Mapped[Tenant | None] = relationship(back_populates="users")
    role: Mapped[Role] = relationship(back_populates="users")
    supplier: Mapped["Supplier | None"] = relationship(back_populates="users")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    bitacora: Mapped[list["Bitacora"]] = relationship(back_populates="user")
    branches: Mapped[list["Branch"]] = relationship(secondary="usuario_sucursales", back_populates="users")


class UserBranch(Base):
    __tablename__ = "usuario_sucursales"
    __table_args__ = (PrimaryKeyConstraint("user_id", "branch_id"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    branch_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id", ondelete="CASCADE"))


class RefreshToken(Base):
    __tablename__ = "sesiones_actualizacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="refresh_tokens")


class City(Base):
    __tablename__ = "ciudades"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    branches: Mapped[list["Branch"]] = relationship(back_populates="city")


class Branch(Base):
    __tablename__ = "sucursales"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("ciudades.id", ondelete="RESTRICT"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    tenant: Mapped[Tenant | None] = relationship(back_populates="branches")
    city: Mapped[City] = relationship(back_populates="branches")
    inventory: Mapped[list["Inventory"]] = relationship(back_populates="branch")
    users: Mapped[list[User]] = relationship(secondary="usuario_sucursales", back_populates="branches")


class Category(Base):
    __tablename__ = "categorias"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_categories_tenant_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    tenant: Mapped[Tenant | None] = relationship(back_populates="categories")
    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Size(Base):
    __tablename__ = "tallas"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    size_type: Mapped[str] = mapped_column(String(16), nullable=False, default="ALPHA", server_default="ALPHA")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    variants: Mapped[list["ProductVariant"]] = relationship(back_populates="size")


class Color(Base):
    __tablename__ = "colores"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hex_code: Mapped[str | None] = mapped_column(String(7))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    variants: Mapped[list["ProductVariant"]] = relationship(back_populates="color")


class Supplier(Base):
    __tablename__ = "proveedores"
    __table_args__ = (UniqueConstraint("tenant_id", "tax_id", name="uq_suppliers_tenant_tax_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    trade_name: Mapped[str] = mapped_column(String(150), nullable=False)
    legal_name: Mapped[str | None] = mapped_column(String(200))
    tax_id: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(30))
    address: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    tenant: Mapped[Tenant | None] = relationship(back_populates="suppliers")
    products: Mapped[list["ProductSupplier"]] = relationship(back_populates="supplier")
    users: Mapped[list[User]] = relationship(back_populates="supplier")
    supply_offers: Mapped[list["SupplierSupplyOffer"]] = relationship(back_populates="supplier", cascade="all, delete-orphan")


class Season(Base):
    __tablename__ = "temporadas"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_seasons_tenant_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    starts_on: Mapped[date | None] = mapped_column(Date)
    ends_on: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    tenant: Mapped[Tenant | None] = relationship(back_populates="seasons")
    collections: Mapped[list["Collection"]] = relationship(back_populates="season")
    products: Mapped[list["Product"]] = relationship(back_populates="season")


class Collection(Base):
    __tablename__ = "colecciones"
    __table_args__ = (UniqueConstraint("season_id", "name", name="uq_collections_season_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("temporadas.id", ondelete="RESTRICT"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    tenant: Mapped[Tenant | None] = relationship(back_populates="collections")
    season: Mapped[Season] = relationship(back_populates="collections")
    products: Mapped[list["Product"]] = relationship(back_populates="collection")


class Product(Base):
    __tablename__ = "productos"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_products_tenant_code"),
        UniqueConstraint("tenant_id", "slug", name="uq_products_tenant_slug"),
        Index("ix_productos_name", "name"),
        Index("ix_productos_tenant_name", "tenant_id", "name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categorias.id", ondelete="RESTRICT"), nullable=False, index=True)
    season_id: Mapped[int | None] = mapped_column(ForeignKey("temporadas.id", ondelete="RESTRICT"), index=True)
    collection_id: Mapped[int | None] = mapped_column(ForeignKey("colecciones.id", ondelete="RESTRICT"), index=True)
    audience: Mapped[str] = mapped_column(String(16), nullable=False, default="UNISEX", server_default="UNISEX", index=True)
    size_system: Mapped[str] = mapped_column(String(16), nullable=False, default="ALPHA", server_default="ALPHA", index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    tenant: Mapped[Tenant | None] = relationship(back_populates="products")
    category: Mapped[Category] = relationship(back_populates="products")
    season: Mapped[Season | None] = relationship(back_populates="products")
    collection: Mapped[Collection | None] = relationship(back_populates="products")
    variants: Mapped[list["ProductVariant"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    images: Mapped[list["ProductImage"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    suppliers: Mapped[list["ProductSupplier"]] = relationship(back_populates="product", cascade="all, delete-orphan")


class ProductSupplier(Base):
    __tablename__ = "producto_proveedores"
    __table_args__ = (PrimaryKeyConstraint("product_id", "supplier_id"),)

    product_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="CASCADE"))
    supplier_id: Mapped[int] = mapped_column(ForeignKey("proveedores.id", ondelete="RESTRICT"))

    product: Mapped[Product] = relationship(back_populates="suppliers")
    supplier: Mapped[Supplier] = relationship(back_populates="products")


class SupplierSupplyOffer(Base):
    __tablename__ = "ofertas_abastecimiento"
    __table_args__ = (
        CheckConstraint("available_quantity >= 0", name="ck_supply_offer_quantity_nonnegative"),
        CheckConstraint("status IN ('AVAILABLE', 'LIMITED', 'OUT_OF_STOCK', 'UPCOMING')", name="ck_supply_offer_status"),
        Index("ix_supply_offer_supplier", "supplier_id"),
        Index("ix_supply_offer_variant", "product_variant_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("proveedores.id", ondelete="CASCADE"), nullable=False)
    product_variant_id: Mapped[int] = mapped_column(ForeignKey("variantes_producto.id", ondelete="RESTRICT"), nullable=False)
    season_id: Mapped[int] = mapped_column(ForeignKey("temporadas.id", ondelete="RESTRICT"), nullable=False)
    collection_id: Mapped[int | None] = mapped_column(ForeignKey("colecciones.id", ondelete="RESTRICT"))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="AVAILABLE", server_default="AVAILABLE")
    available_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    expected_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    tenant: Mapped[Tenant | None] = relationship(back_populates="supply_offers")
    supplier: Mapped[Supplier] = relationship(back_populates="supply_offers")
    product_variant: Mapped["ProductVariant"] = relationship(back_populates="supply_offers")
    season: Mapped[Season] = relationship()
    collection: Mapped[Collection | None] = relationship()


class ProductVariant(Base):
    __tablename__ = "variantes_producto"
    __table_args__ = (
        UniqueConstraint("product_id", "size_id", "color_id", name="uq_product_variant_attributes"),
        UniqueConstraint("tenant_id", "sku", name="uq_product_variants_tenant_sku"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="CASCADE"), nullable=False, index=True)
    size_id: Mapped[int] = mapped_column(ForeignKey("tallas.id", ondelete="RESTRICT"), nullable=False)
    color_id: Mapped[int] = mapped_column(ForeignKey("colores.id", ondelete="RESTRICT"), nullable=False)
    sku: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    tenant: Mapped[Tenant | None] = relationship(back_populates="product_variants")
    product: Mapped[Product] = relationship(back_populates="variants")
    size: Mapped[Size] = relationship(back_populates="variants")
    color: Mapped[Color] = relationship(back_populates="variants")
    inventory: Mapped[list["Inventory"]] = relationship(back_populates="product_variant")
    supply_offers: Mapped[list["SupplierSupplyOffer"]] = relationship(back_populates="product_variant")


class ProductImage(Base):
    __tablename__ = "imagenes_producto"
    __table_args__ = (UniqueConstraint("product_id", "sort_order", name="uq_product_image_order"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="CASCADE"), nullable=False, index=True)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    product: Mapped[Product] = relationship(back_populates="images")


class Inventory(Base):
    __tablename__ = "inventario"
    __table_args__ = (
        UniqueConstraint("branch_id", "product_variant_id", name="uq_inventory_branch_variant"),
        Index("ix_inventory_tenant_branch", "tenant_id", "branch_id"),
        CheckConstraint("stock_quantity >= 0", name="ck_inventory_stock_nonnegative"),
        CheckConstraint("reserved_quantity >= 0 AND reserved_quantity <= stock_quantity", name="ck_inventory_reserved_valid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id", ondelete="RESTRICT"), nullable=False, index=True)
    product_variant_id: Mapped[int] = mapped_column(ForeignKey("variantes_producto.id", ondelete="RESTRICT"), nullable=False, index=True)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    tenant: Mapped[Tenant | None] = relationship(back_populates="inventories")
    branch: Mapped[Branch] = relationship(back_populates="inventory")
    product_variant: Mapped[ProductVariant] = relationship(back_populates="inventory")
    movements: Mapped[list["InventoryMovement"]] = relationship(back_populates="inventory")
    quarantine_records: Mapped[list["InventoryQuarantine"]] = relationship(back_populates="inventory")


class Reservation(Base):
    __tablename__ = "reservas"
    __table_args__ = (
        Index("ix_reservations_customer_status", "customer_id", "status"),
        Index("ix_reservations_tenant_branch_status", "tenant_id", "branch_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id", ondelete="RESTRICT"), nullable=False, index=True)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    tenant: Mapped[Tenant | None] = relationship(back_populates="reservations")
    customer: Mapped[User] = relationship()
    branch: Mapped[Branch] = relationship()
    items: Mapped[list["ReservationItem"]] = relationship(back_populates="reservation", cascade="all, delete-orphan")


class ReservationItem(Base):
    __tablename__ = "detalles_reserva"
    __table_args__ = (
        UniqueConstraint("reservation_id", "product_variant_id", name="uq_reservation_variant"),
        CheckConstraint("quantity > 0", name="ck_reservation_item_quantity_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    reservation_id: Mapped[int] = mapped_column(ForeignKey("reservas.id", ondelete="CASCADE"), nullable=False, index=True)
    product_variant_id: Mapped[int] = mapped_column(ForeignKey("variantes_producto.id", ondelete="RESTRICT"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    reservation: Mapped[Reservation] = relationship(back_populates="items")
    product_variant: Mapped[ProductVariant] = relationship()


class Cart(Base):
    __tablename__ = "carritos"
    __table_args__ = (UniqueConstraint("tenant_id", "customer_id", name="uq_carts_tenant_customer"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    tenant: Mapped[Tenant | None] = relationship(back_populates="carts")
    customer: Mapped[User] = relationship()
    items: Mapped[list["CartItem"]] = relationship(back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = "detalles_carrito"
    __table_args__ = (UniqueConstraint("cart_id", "product_variant_id", name="uq_cart_variant"), CheckConstraint("quantity > 0", name="ck_cart_item_quantity_positive"))

    id: Mapped[int] = mapped_column(primary_key=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carritos.id", ondelete="CASCADE"), nullable=False, index=True)
    product_variant_id: Mapped[int] = mapped_column(ForeignKey("variantes_producto.id", ondelete="RESTRICT"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    cart: Mapped[Cart] = relationship(back_populates="items")
    product_variant: Mapped[ProductVariant] = relationship()


class Sale(Base):
    __tablename__ = "ventas"
    __table_args__ = (
        UniqueConstraint("tenant_id", "order_number", name="uq_sales_tenant_order_number"),
        Index("ix_sales_customer_created", "customer_id", "created_at"),
        Index("ix_sales_tenant_created", "tenant_id", "created_at"),
        CheckConstraint("fulfillment_type IN ('PICKUP', 'DELIVERY')", name="ck_sales_fulfillment_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    order_number: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), index=True)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("sucursales.id", ondelete="RESTRICT"), index=True)
    cashier_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), index=True)
    reservation_id: Mapped[int | None] = mapped_column(ForeignKey("reservas.id", ondelete="RESTRICT"), index=True)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    fulfillment_type: Mapped[str] = mapped_column(String(20), default="PICKUP", server_default="PICKUP", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    tenant: Mapped[Tenant | None] = relationship(back_populates="sales")
    items: Mapped[list["SaleItem"]] = relationship(back_populates="sale", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship(back_populates="sale", cascade="all, delete-orphan")
    shipping_snapshot: Mapped["SaleShippingSnapshot | None"] = relationship(back_populates="sale", cascade="all, delete-orphan", uselist=False)
    garment_exchanges: Mapped[list["GarmentExchange"]] = relationship(back_populates="sale", cascade="all, delete-orphan")
    devoluciones: Mapped[list["Devolucion"]] = relationship(back_populates="sale", cascade="all, delete-orphan")


class SaleShippingSnapshot(Base):
    __tablename__ = "envios_venta"

    id: Mapped[int] = mapped_column(primary_key=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("ventas.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    recipient_name: Mapped[str] = mapped_column(String(120), nullable=False)
    recipient_ci: Mapped[str] = mapped_column(String(30), nullable=False)
    recipient_phone: Mapped[str] = mapped_column(String(30), nullable=False)
    department_or_city: Mapped[str] = mapped_column(String(100), nullable=False)
    zone: Mapped[str] = mapped_column(String(120), nullable=False)
    street: Mapped[str] = mapped_column(String(150), nullable=False)
    house_number: Mapped[str] = mapped_column(String(50), nullable=False)
    reference: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    sale: Mapped[Sale] = relationship(back_populates="shipping_snapshot")


class SaleItem(Base):
    __tablename__ = "detalles_venta"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_sale_item_quantity_positive"),
        CheckConstraint("line_total >= 0", name="ck_sale_item_total_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("ventas.id", ondelete="CASCADE"), nullable=False, index=True)
    product_variant_id: Mapped[int] = mapped_column(ForeignKey("variantes_producto.id", ondelete="RESTRICT"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    sale: Mapped[Sale] = relationship(back_populates="items")
    product_variant: Mapped[ProductVariant] = relationship()


class GarmentExchange(Base):
    __tablename__ = "garment_exchanges"
    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_garment_exchanges_tenant_idempotency"),
        CheckConstraint("returned_value >= 0 AND delivered_value >= 0", name="ck_garment_exchange_values_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("ventas.id", ondelete="RESTRICT"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id", ondelete="RESTRICT"), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(100), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="EXCHANGED", server_default="EXCHANGED")
    returned_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    delivered_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    difference: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cash_tendered: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    cash_change: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    cash_refunded: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    cashier_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    result_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant: Mapped[Tenant | None] = relationship(back_populates="garment_exchanges")
    sale: Mapped[Sale] = relationship(back_populates="garment_exchanges")
    items: Mapped[list["GarmentExchangeItem"]] = relationship(back_populates="exchange", cascade="all, delete-orphan")


class GarmentExchangeItem(Base):
    __tablename__ = "garment_exchange_items"
    __table_args__ = (UniqueConstraint("exchange_id", "sale_item_id", name="uq_garment_exchange_item_sale_item"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    exchange_id: Mapped[int] = mapped_column(ForeignKey("garment_exchanges.id", ondelete="CASCADE"), nullable=False, index=True)
    sale_item_id: Mapped[int] = mapped_column(ForeignKey("detalles_venta.id", ondelete="RESTRICT"), nullable=False, index=True)
    returned_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    new_variant_id: Mapped[int] = mapped_column(ForeignKey("variantes_producto.id", ondelete="RESTRICT"), nullable=False)
    new_quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    exchange: Mapped[GarmentExchange] = relationship(back_populates="items")
    sale_item: Mapped[SaleItem] = relationship()
    new_variant: Mapped[ProductVariant] = relationship()
    quarantine: Mapped["InventoryQuarantine | None"] = relationship(back_populates="exchange_item", uselist=False)


class InventoryQuarantine(Base):
    __tablename__ = "inventory_quarantine"
    __table_args__ = (
        UniqueConstraint("exchange_item_id", name="uq_inventory_quarantine_exchange_item"),
        CheckConstraint("quantity > 0", name="ck_inventory_quarantine_quantity_positive"),
        CheckConstraint("status IN ('PENDING', 'RELEASED', 'REJECTED')", name="ck_inventory_quarantine_status_valid"),
        Index("ix_inventory_quarantine_tenant_branch_status", "tenant_id", "branch_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id", ondelete="RESTRICT"), nullable=False, index=True)
    inventory_id: Mapped[int] = mapped_column(ForeignKey("inventario.id", ondelete="RESTRICT"), nullable=False, index=True)
    product_variant_id: Mapped[int] = mapped_column(ForeignKey("variantes_producto.id", ondelete="RESTRICT"), nullable=False, index=True)
    exchange_item_id: Mapped[int] = mapped_column(ForeignKey("garment_exchange_items.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", server_default="PENDING")
    inspected_by: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))
    inspection_reason: Mapped[str | None] = mapped_column(String(255))
    inspected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="quarantine_records")
    branch: Mapped[Branch] = relationship()
    inventory: Mapped[Inventory] = relationship(back_populates="quarantine_records")
    product_variant: Mapped[ProductVariant] = relationship()
    exchange_item: Mapped[GarmentExchangeItem] = relationship(back_populates="quarantine")
    inspector: Mapped[User | None] = relationship()


class Devolucion(Base):
    __tablename__ = "devoluciones"
    __table_args__ = (
        UniqueConstraint("tenant_id", "numero_devolucion", name="uq_devoluciones_tenant_numero"),
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_devoluciones_tenant_idempotency_key"),
        UniqueConstraint("tenant_id", "codigo_nota_credito", name="uq_devoluciones_tenant_credit_note_code"),
        CheckConstraint("total_devuelto >= 0", name="ck_devoluciones_total_nonnegative"),
        CheckConstraint("tipo_reembolso IN ('EFECTIVO', 'NOTA_CREDITO')", name="ck_devoluciones_tipo_reembolso_valid"),
        CheckConstraint("estado IN ('SOLICITADA', 'APROBADA', 'RECHAZADA', 'COMPLETADA')", name="ck_devoluciones_estado_valid"),
        Index("ix_devoluciones_tenant_created", "tenant_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    sucursal_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id", ondelete="RESTRICT"), nullable=False, index=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("ventas.id", ondelete="RESTRICT"), nullable=False, index=True)
    cajero_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True)
    autorizado_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)
    numero_devolucion: Mapped[str] = mapped_column(String(50), nullable=False)
    total_devuelto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    tipo_reembolso: Mapped[str] = mapped_column(String(30), nullable=False, default="EFECTIVO")
    codigo_nota_credito: Mapped[str | None] = mapped_column(String(50), nullable=True)
    beneficiario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=True, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    request_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    saldo_nota_credito: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    motivo: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="SOLICITADA")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    tenant: Mapped[Tenant] = relationship()
    branch: Mapped[Branch] = relationship()
    sale: Mapped[Sale] = relationship(back_populates="devoluciones")
    cashier: Mapped[User] = relationship(foreign_keys=[cajero_id])
    authorized_by: Mapped[User | None] = relationship(foreign_keys=[autorizado_por])
    beneficiario: Mapped[User | None] = relationship(foreign_keys=[beneficiario_id])
    detalles: Mapped[list["DetalleDevolucion"]] = relationship(back_populates="devolucion", cascade="all, delete-orphan")
    redemptions: Mapped[list["CreditNoteRedemption"]] = relationship(back_populates="credit_note")


class CreditNoteRedemption(Base):
    __tablename__ = "credit_note_redemptions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_credit_note_redemptions_tenant_key"),
        CheckConstraint("applied_amount > 0", name="ck_credit_note_redemptions_amount_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    credit_note_id: Mapped[int] = mapped_column(ForeignKey("devoluciones.id", ondelete="RESTRICT"), nullable=False, index=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("ventas.id", ondelete="RESTRICT"), nullable=False, index=True)
    cashier_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("pagos.id", ondelete="RESTRICT"), nullable=False, unique=True)
    idempotency_key: Mapped[str] = mapped_column(String(100), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    applied_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    post_redemption_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="credit_note_redemptions")
    credit_note: Mapped[Devolucion] = relationship(back_populates="redemptions")
    sale: Mapped[Sale] = relationship()
    cashier: Mapped[User] = relationship()
    payment: Mapped["Payment"] = relationship()


class DetalleDevolucion(Base):
    __tablename__ = "detalles_devolucion"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="ck_detalles_devolucion_cantidad_positive"),
        CheckConstraint("subtotal >= 0", name="ck_detalles_devolucion_subtotal_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    devolucion_id: Mapped[int] = mapped_column(ForeignKey("devoluciones.id", ondelete="CASCADE"), nullable=False, index=True)
    detalle_venta_id: Mapped[int] = mapped_column(ForeignKey("detalles_venta.id", ondelete="RESTRICT"), nullable=False, index=True)
    variante_producto_id: Mapped[int] = mapped_column(ForeignKey("variantes_producto.id", ondelete="RESTRICT"), nullable=False, index=True)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    estado_prenda: Mapped[str] = mapped_column(String(50), nullable=False, default="IMPECABLE")
    reintegrado_inventario: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    devolucion: Mapped[Devolucion] = relationship(back_populates="detalles")
    sale_item: Mapped[SaleItem] = relationship()
    product_variant: Mapped[ProductVariant] = relationship()


class Payment(Base):
    __tablename__ = "pagos"
    __table_args__ = (
        UniqueConstraint("tenant_id", "provider", "transaction_reference", name="uq_payments_tenant_provider_reference"),
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_payments_tenant_idempotency_key"),
        CheckConstraint("amount >= 0", name="ck_payment_amount_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(100), index=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("ventas.id", ondelete="RESTRICT"), nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(30), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(50))
    transaction_reference: Mapped[str | None] = mapped_column(String(150))
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    received_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    change_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant: Mapped[Tenant | None] = relationship(back_populates="payments")
    sale: Mapped[Sale] = relationship(back_populates="payments")


class InventoryMovement(Base):
    __tablename__ = "movimientos_inventario"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_inventory_movement_quantity_positive"),
        CheckConstraint("stock_before >= 0 AND stock_after >= 0", name="ck_inventory_movement_stock_nonnegative"),
        CheckConstraint("movement_type IN ('IN', 'OUT', 'RETURN', 'RESTOCK', 'RESERVE', 'RELEASE', 'SALE')", name="ck_inventory_movement_type_valid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    inventory_id: Mapped[int] = mapped_column(ForeignKey("inventario.id", ondelete="RESTRICT"), nullable=False, index=True)
    movement_type: Mapped[str] = mapped_column(String(30), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_before: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255))
    reference_type: Mapped[str | None] = mapped_column(String(50))
    reference_id: Mapped[int | None] = mapped_column(Integer)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant: Mapped[Tenant | None] = relationship(back_populates="inventory_movements")
    inventory: Mapped[Inventory] = relationship(back_populates="movements")
    creator: Mapped[User | None] = relationship()


class Promotion(Base):
    __tablename__ = "promociones"
    __table_args__ = (
        CheckConstraint("discount_value > 0", name="ck_promotion_discount_positive"),
        CheckConstraint("ends_at > starts_at", name="ck_promotion_dates_valid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    discount_type: Mapped[str] = mapped_column(String(20), nullable=False)
    discount_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    tenant: Mapped[Tenant | None] = relationship(back_populates="promotions")
    products: Mapped[list["PromotionProduct"]] = relationship(back_populates="promotion", cascade="all, delete-orphan")


class PromotionProduct(Base):
    __tablename__ = "productos_promocion"
    __table_args__ = (PrimaryKeyConstraint("promotion_id", "product_id"),)

    promotion_id: Mapped[int] = mapped_column(ForeignKey("promociones.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="CASCADE"))

    promotion: Mapped[Promotion] = relationship(back_populates="products")
    product: Mapped[Product] = relationship()


class VirtualFittingSession(Base):
    __tablename__ = "sesiones_vestidor_virtual"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="RESTRICT"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="STARTED", nullable=False)
    device_info: Mapped[str | None] = mapped_column(String(255))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    tenant: Mapped[Tenant | None] = relationship(back_populates="virtual_fitting_sessions")
    product: Mapped[Product] = relationship()


class AIRecommendation(Base):
    __tablename__ = "recomendaciones_ia"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="RESTRICT"), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    context: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    tenant: Mapped[Tenant | None] = relationship(back_populates="ai_recommendations")


class Bitacora(Base):
    """Auditoria transversal de cambios y eventos relevantes de la plataforma."""

    __tablename__ = "bitacora"
    __table_args__ = (
        Index("ix_bitacora_entity", "tipo_entidad", "entidad_id"),
        Index("ix_bitacora_created_at", "fecha_creacion"),
        Index("ix_bitacora_tenant_created_at", "tenant_id", "fecha_creacion"),
        Index("ix_bitacora_tenant_entity", "tenant_id", "tipo_entidad", "entidad_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column("tenant_id", ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id: Mapped[int | None] = mapped_column("usuario_id", ForeignKey("usuarios.id", ondelete="SET NULL"), index=True)
    action: Mapped[str] = mapped_column("accion", String(30), nullable=False)
    entity_type: Mapped[str] = mapped_column("tipo_entidad", String(100), nullable=False)
    entity_id: Mapped[int | None] = mapped_column("entidad_id", Integer)
    description: Mapped[str | None] = mapped_column("descripcion", Text)
    old_values: Mapped[dict | None] = mapped_column("valores_anteriores", JSON)
    new_values: Mapped[dict | None] = mapped_column("valores_nuevos", JSON)
    ip_address: Mapped[str | None] = mapped_column("direccion_ip", String(45))
    user_agent: Mapped[str | None] = mapped_column("agente_usuario", String(500))
    created_at: Mapped[datetime] = mapped_column("fecha_creacion", DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant: Mapped[Tenant | None] = relationship(back_populates="bitacoras")
    user: Mapped[User | None] = relationship(back_populates="bitacora")


class SyncOperation(Base):
    __tablename__ = "sync_operations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "client_operation_id", name="uq_sync_operations_tenant_client_op_id"),
        Index("ix_sync_operations_tenant_created", "tenant_id", "created_at"),
        CheckConstraint("operation_type IN ('SALE', 'RESERVATION')", name="ck_sync_operations_type"),
        CheckConstraint("status IN ('CONFIRMED', 'CONFLICT', 'REJECTED')", name="ck_sync_operations_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    client_operation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id", ondelete="RESTRICT"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True)
    operation_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    conflict_detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    sale_id: Mapped[int | None] = mapped_column(ForeignKey("ventas.id", ondelete="SET NULL"), nullable=True, index=True)
    reservation_id: Mapped[int | None] = mapped_column(ForeignKey("reservas.id", ondelete="SET NULL"), nullable=True, index=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="sync_operations")
    branch: Mapped[Branch] = relationship()
    user: Mapped[User] = relationship()
    sale: Mapped["Sale | None"] = relationship()
    reservation: Mapped["Reservation | None"] = relationship()
