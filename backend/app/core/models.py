from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import JSON, Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric, PrimaryKeyConstraint, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


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
    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False, index=True)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("proveedores.id", ondelete="SET NULL"), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

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
    __table_args__ = (UniqueConstraint("city_id", "name", name="uq_branches_city_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("ciudades.id", ondelete="RESTRICT"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    city: Mapped[City] = relationship(back_populates="branches")
    inventory: Mapped[list["Inventory"]] = relationship(back_populates="branch")
    users: Mapped[list[User]] = relationship(secondary="usuario_sucursales", back_populates="branches")


class Category(Base):
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

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

    id: Mapped[int] = mapped_column(primary_key=True)
    trade_name: Mapped[str] = mapped_column(String(150), nullable=False)
    legal_name: Mapped[str | None] = mapped_column(String(200))
    tax_id: Mapped[str | None] = mapped_column(String(50), unique=True)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(30))
    address: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    products: Mapped[list["ProductSupplier"]] = relationship(back_populates="supplier")
    users: Mapped[list[User]] = relationship(back_populates="supplier")
    supply_offers: Mapped[list["SupplierSupplyOffer"]] = relationship(back_populates="supplier", cascade="all, delete-orphan")


class Season(Base):
    __tablename__ = "temporadas"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    starts_on: Mapped[date | None] = mapped_column(Date)
    ends_on: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    collections: Mapped[list["Collection"]] = relationship(back_populates="season")
    products: Mapped[list["Product"]] = relationship(back_populates="season")


class Collection(Base):
    __tablename__ = "colecciones"
    __table_args__ = (UniqueConstraint("season_id", "name", name="uq_collections_season_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("temporadas.id", ondelete="RESTRICT"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    season: Mapped[Season] = relationship(back_populates="collections")
    products: Mapped[list["Product"]] = relationship(back_populates="collection")


class Product(Base):
    __tablename__ = "productos"
    __table_args__ = (Index("ix_productos_name", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categorias.id", ondelete="RESTRICT"), nullable=False, index=True)
    season_id: Mapped[int | None] = mapped_column(ForeignKey("temporadas.id", ondelete="RESTRICT"), index=True)
    collection_id: Mapped[int | None] = mapped_column(ForeignKey("colecciones.id", ondelete="RESTRICT"), index=True)
    audience: Mapped[str] = mapped_column(String(16), nullable=False, default="UNISEX", server_default="UNISEX", index=True)
    size_system: Mapped[str] = mapped_column(String(16), nullable=False, default="ALPHA", server_default="ALPHA", index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

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

    supplier: Mapped[Supplier] = relationship(back_populates="supply_offers")
    product_variant: Mapped["ProductVariant"] = relationship(back_populates="supply_offers")
    season: Mapped[Season] = relationship()
    collection: Mapped[Collection | None] = relationship()


class ProductVariant(Base):
    __tablename__ = "variantes_producto"
    __table_args__ = (
        UniqueConstraint("product_id", "size_id", "color_id", name="uq_product_variant_attributes"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="CASCADE"), nullable=False, index=True)
    size_id: Mapped[int] = mapped_column(ForeignKey("tallas.id", ondelete="RESTRICT"), nullable=False)
    color_id: Mapped[int] = mapped_column(ForeignKey("colores.id", ondelete="RESTRICT"), nullable=False)
    sku: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

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
        CheckConstraint("stock_quantity >= 0", name="ck_inventory_stock_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id", ondelete="RESTRICT"), nullable=False, index=True)
    product_variant_id: Mapped[int] = mapped_column(ForeignKey("variantes_producto.id", ondelete="RESTRICT"), nullable=False, index=True)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    branch: Mapped[Branch] = relationship(back_populates="inventory")
    product_variant: Mapped[ProductVariant] = relationship(back_populates="inventory")
    movements: Mapped[list["InventoryMovement"]] = relationship(back_populates="inventory")


class Reservation(Base):
    __tablename__ = "reservas"
    __table_args__ = (Index("ix_reservations_customer_status", "customer_id", "status"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id", ondelete="RESTRICT"), nullable=False, index=True)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

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

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

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
    __table_args__ = (Index("ix_sales_customer_created", "customer_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), index=True)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("sucursales.id", ondelete="RESTRICT"), index=True)
    cashier_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), index=True)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    items: Mapped[list["SaleItem"]] = relationship(back_populates="sale", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship(back_populates="sale", cascade="all, delete-orphan")


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


class Payment(Base):
    __tablename__ = "pagos"
    __table_args__ = (
        UniqueConstraint("provider", "transaction_reference", name="uq_payment_provider_reference"),
        CheckConstraint("amount >= 0", name="ck_payment_amount_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("ventas.id", ondelete="RESTRICT"), nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(30), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(50))
    transaction_reference: Mapped[str | None] = mapped_column(String(150))
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    sale: Mapped[Sale] = relationship(back_populates="payments")


class InventoryMovement(Base):
    __tablename__ = "movimientos_inventario"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_inventory_movement_quantity_positive"),
        CheckConstraint("stock_before >= 0 AND stock_after >= 0", name="ck_inventory_movement_stock_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    inventory_id: Mapped[int] = mapped_column(ForeignKey("inventario.id", ondelete="RESTRICT"), nullable=False, index=True)
    movement_type: Mapped[str] = mapped_column(String(30), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_before: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    inventory: Mapped[Inventory] = relationship(back_populates="movements")
    creator: Mapped[User | None] = relationship()


class Promotion(Base):
    __tablename__ = "promociones"
    __table_args__ = (
        CheckConstraint("discount_value > 0", name="ck_promotion_discount_positive"),
        CheckConstraint("ends_at > starts_at", name="ck_promotion_dates_valid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    discount_type: Mapped[str] = mapped_column(String(20), nullable=False)
    discount_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

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
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="RESTRICT"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="STARTED", nullable=False)
    device_info: Mapped[str | None] = mapped_column(String(255))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AIRecommendation(Base):
    __tablename__ = "recomendaciones_ia"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="RESTRICT"), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    context: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Bitacora(Base):
    """Auditoria transversal de cambios y eventos relevantes de la plataforma."""

    __tablename__ = "bitacora"
    __table_args__ = (
        Index("ix_bitacora_entity", "tipo_entidad", "entidad_id"),
        Index("ix_bitacora_created_at", "fecha_creacion"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
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

    user: Mapped[User | None] = relationship(back_populates="bitacora")
