from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.audit import record_audit
from app.core.models import Branch, Cart, CartItem, Inventory, InventoryMovement, Payment, ProductVariant, Sale, SaleItem, User
from app.modules.commerce.schemas import CartItemRequest, CartItemUpdateRequest, CashPaymentRequest, DigitalPurchaseRequest, ElectronicNotificationRequest, ElectronicPaymentRequest, PhysicalSaleRequest
from app.modules.inventory.service import get_locked_inventory


def error(code: str, message: str, http_status: int = status.HTTP_400_BAD_REQUEST) -> HTTPException:
    return HTTPException(status_code=http_status, detail={"code": code, "message": message})


def cart_query():
    return select(Cart).options(
        joinedload(Cart.items).joinedload(CartItem.product_variant).joinedload(ProductVariant.product),
        joinedload(Cart.items).joinedload(CartItem.product_variant).joinedload(ProductVariant.size),
        joinedload(Cart.items).joinedload(CartItem.product_variant).joinedload(ProductVariant.color),
    )


def get_cart(db: Session, customer_id: int) -> Cart:
    cart = db.execute(cart_query().where(Cart.customer_id == customer_id, Cart.status == "ACTIVE")).unique().scalar_one_or_none()
    if cart is None:
        cart = Cart(customer_id=customer_id, status="ACTIVE")
        db.add(cart)
        db.flush()
        cart = db.execute(cart_query().where(Cart.id == cart.id)).unique().scalar_one()
    return cart


def _available(db: Session, branch_id: int, variant_id: int) -> int:
    inventory = db.scalar(select(Inventory).where(Inventory.branch_id == branch_id, Inventory.product_variant_id == variant_id))
    return inventory.stock_quantity - inventory.reserved_quantity if inventory else 0


def serialize_cart(cart: Cart, db: Session) -> dict[str, object]:
    items = []
    for item in cart.items:
        variant = item.product_variant
        available = max(_available_any_branch(db, variant.id), 0)
        items.append({"id": item.id, "product_variant_id": variant.id, "product_id": variant.product_id, "product_name": variant.product.name, "sku": variant.sku, "size_name": variant.size.name, "color_name": variant.color.name, "quantity": item.quantity, "unit_price": item.unit_price, "line_total": item.unit_price * item.quantity, "available_quantity": available})
    subtotal = sum((item["line_total"] for item in items), Decimal("0"))
    return {"id": cart.id, "customer_id": cart.customer_id, "status": cart.status, "items": items, "subtotal": subtotal, "total": subtotal, "updated_at": cart.updated_at}


def _available_any_branch(db: Session, variant_id: int) -> int:
    return db.scalar(select(func.coalesce(func.sum(Inventory.stock_quantity - Inventory.reserved_quantity), 0)).where(Inventory.product_variant_id == variant_id)) or 0


def add_cart_item(db: Session, customer_id: int, data: CartItemRequest) -> Cart:
    cart = get_cart(db, customer_id)
    variant = db.scalar(select(ProductVariant).options(joinedload(ProductVariant.product)).where(ProductVariant.id == data.product_variant_id, ProductVariant.is_active.is_(True)))
    if variant is None or not variant.product.is_active:
        raise error("VARIANT_NOT_FOUND_OR_INACTIVE", "La variante no existe o está inactiva.")
    item = next((item for item in cart.items if item.product_variant_id == data.product_variant_id), None)
    target_quantity = data.quantity + item.quantity if item else data.quantity
    if target_quantity > _available_any_branch(db, data.product_variant_id):
        raise error("INSUFFICIENT_STOCK", "La cantidad supera la disponibilidad actual.", status.HTTP_409_CONFLICT)
    if item:
        item.quantity = target_quantity
    else:
        cart.items.append(CartItem(product_variant_id=data.product_variant_id, quantity=data.quantity, unit_price=variant.product.price))
    db.flush()
    return get_cart(db, customer_id)


def update_cart_item(db: Session, customer_id: int, item_id: int, data: CartItemUpdateRequest) -> Cart:
    cart = get_cart(db, customer_id)
    item = next((item for item in cart.items if item.id == item_id), None)
    if item is None:
        raise error("CART_ITEM_NOT_FOUND", "Artículo no encontrado en el carrito.", status.HTTP_404_NOT_FOUND)
    if data.quantity > _available_any_branch(db, item.product_variant_id):
        raise error("INSUFFICIENT_STOCK", "La cantidad supera la disponibilidad actual.", status.HTTP_409_CONFLICT)
    item.quantity = data.quantity
    db.flush()
    return get_cart(db, customer_id)


def remove_cart_item(db: Session, customer_id: int, item_id: int) -> Cart:
    cart = get_cart(db, customer_id)
    item = next((item for item in cart.items if item.id == item_id), None)
    if item is None:
        raise error("CART_ITEM_NOT_FOUND", "Artículo no encontrado en el carrito.", status.HTTP_404_NOT_FOUND)
    db.delete(item)
    db.flush()
    return get_cart(db, customer_id)


def clear_cart(db: Session, customer_id: int) -> Cart:
    cart = get_cart(db, customer_id)
    cart.items.clear()
    db.flush()
    return get_cart(db, customer_id)


def sale_query():
    return select(Sale).options(
        joinedload(Sale.items).joinedload(SaleItem.product_variant).joinedload(ProductVariant.product),
        joinedload(Sale.payments),
    )


def get_sale(db: Session, sale_id: int) -> Sale:
    sale = db.execute(sale_query().where(Sale.id == sale_id)).unique().scalar_one_or_none()
    if sale is None:
        raise error("SALE_NOT_FOUND", "Venta no encontrada.", status.HTTP_404_NOT_FOUND)
    return sale


def serialize_sale(sale: Sale) -> dict[str, object]:
    return {"id": sale.id, "order_number": sale.order_number, "customer_id": sale.customer_id, "branch_id": sale.branch_id, "cashier_id": sale.cashier_id, "channel": sale.channel, "status": sale.status, "subtotal": sale.subtotal, "discount": sale.discount, "total": sale.total, "created_at": sale.created_at, "items": [{"id": item.id, "product_variant_id": item.product_variant_id, "product_name": item.product_variant.product.name, "sku": item.product_variant.sku, "quantity": item.quantity, "unit_price": item.unit_price, "discount": item.discount, "line_total": item.line_total} for item in sale.items], "payments": [{"id": payment.id, "sale_id": payment.sale_id, "method": payment.method, "provider": payment.provider, "transaction_reference": payment.transaction_reference, "status": payment.status, "amount": payment.amount, "paid_at": payment.paid_at} for payment in sale.payments]}


def serialize_payment(payment: Payment) -> dict[str, object]:
    return {"id": payment.id, "sale_id": payment.sale_id, "method": payment.method, "provider": payment.provider, "transaction_reference": payment.transaction_reference, "status": payment.status, "amount": payment.amount, "paid_at": payment.paid_at}


def _validate_branch(db: Session, branch_id: int) -> Branch:
    branch = db.scalar(select(Branch).where(Branch.id == branch_id, Branch.is_active.is_(True)))
    if branch is None:
        raise error("BRANCH_NOT_FOUND_OR_INACTIVE", "La sucursal no existe o está inactiva.")
    return branch


def _variant(db: Session, variant_id: int) -> ProductVariant:
    variant = db.scalar(select(ProductVariant).options(joinedload(ProductVariant.product)).where(ProductVariant.id == variant_id, ProductVariant.is_active.is_(True)))
    if variant is None or not variant.product.is_active:
        raise error("VARIANT_NOT_FOUND_OR_INACTIVE", "Una variante no existe o está inactiva.")
    return variant


def _new_order_number() -> str:
    return f"FS-{datetime.now(UTC):%Y%m%d}-{uuid4().hex[:8].upper()}"


def _create_sale(db: Session, branch_id: int, channel: str, customer_id: int | None, cashier_id: int | None, items: list[tuple[int, int, Decimal]], discount: Decimal) -> Sale:
    _validate_branch(db, branch_id)
    if discount < 0:
        raise error("INVALID_DISCOUNT", "El descuento no puede ser negativo.")
    sale_items = []
    subtotal = Decimal("0")
    for variant_id, quantity, unit_price in items:
        variant = _variant(db, variant_id)
        inventory = db.scalar(select(Inventory).where(Inventory.branch_id == branch_id, Inventory.product_variant_id == variant_id))
        if inventory is None or inventory.stock_quantity - inventory.reserved_quantity < quantity:
            raise error("INSUFFICIENT_STOCK", f"No existe stock suficiente para {variant.product.name}.", status.HTTP_409_CONFLICT)
        line_total = unit_price * quantity
        subtotal += line_total
        sale_items.append(SaleItem(product_variant_id=variant_id, quantity=quantity, unit_price=unit_price, discount=Decimal("0"), line_total=line_total))
    if discount > subtotal:
        raise error("INVALID_DISCOUNT", "El descuento no puede superar el subtotal.")
    sale = Sale(order_number=_new_order_number(), customer_id=customer_id, branch_id=branch_id, cashier_id=cashier_id, channel=channel, status="PENDING", subtotal=subtotal, discount=discount, total=subtotal - discount, items=sale_items)
    db.add(sale)
    db.flush()
    return get_sale(db, sale.id)


def create_physical_sale(db: Session, data: PhysicalSaleRequest, cashier: User) -> Sale:
    return _create_sale(db, data.branch_id, "PHYSICAL", data.customer_id, cashier.id, [(item.product_variant_id, item.quantity, _variant(db, item.product_variant_id).product.price) for item in data.items], data.discount)


def create_digital_purchase(db: Session, data: DigitalPurchaseRequest, customer: User) -> Sale:
    cart = get_cart(db, customer.id)
    if not cart.items:
        raise error("EMPTY_CART", "No se puede iniciar una compra con el carrito vacío.", status.HTTP_400_BAD_REQUEST)
    items = [(item.product_variant_id, item.quantity, _variant(db, item.product_variant_id).product.price) for item in cart.items]
    return _create_sale(db, data.branch_id, "DIGITAL", customer.id, None, items, data.discount)


def _consume_inventory(db: Session, sale: Sale, user: User | None) -> None:
    for item in sale.items:
        inventory = db.scalar(select(Inventory.id).where(Inventory.branch_id == sale.branch_id, Inventory.product_variant_id == item.product_variant_id))
        if inventory is None:
            raise error("INVENTORY_NOT_FOUND", "Inventario no encontrado.", status.HTTP_409_CONFLICT)
        locked = get_locked_inventory(db, inventory)
        available = locked.stock_quantity - locked.reserved_quantity
        if available < item.quantity:
            raise error("INSUFFICIENT_STOCK", "El stock cambió y ya no es suficiente.", status.HTTP_409_CONFLICT)
        before = locked.stock_quantity
        locked.stock_quantity -= item.quantity
        db.add(InventoryMovement(inventory_id=locked.id, movement_type="SALE", quantity=item.quantity, stock_before=before, stock_after=locked.stock_quantity, reason="Venta confirmada", reference_type="sale", reference_id=sale.id, created_by=user.id if user else None))


def confirm_sale(db: Session, sale: Sale, user: User | None) -> Sale:
    if sale.status == "CONFIRMED":
        return sale
    if sale.status != "PENDING":
        raise error("SALE_NOT_PENDING", "La venta no puede confirmarse en su estado actual.", status.HTTP_409_CONFLICT)
    _consume_inventory(db, sale, user)
    sale.status = "CONFIRMED"
    record_audit(db, user, "UPDATE", "sale", sale.id, "Venta confirmada y descontada del inventario.", new_values={"status": sale.status})
    db.flush()
    return get_sale(db, sale.id)


def process_cash_payment(db: Session, sale: Sale, data: CashPaymentRequest, cashier: User) -> Sale:
    if sale.channel != "PHYSICAL" or sale.status != "PENDING":
        raise error("INVALID_CASH_SALE", "Solo se puede pagar una venta presencial pendiente.", status.HTTP_409_CONFLICT)
    if data.amount < sale.total:
        raise error("INSUFFICIENT_PAYMENT", "El monto recibido no cubre el total de la venta.", status.HTTP_400_BAD_REQUEST)
    payment = Payment(sale_id=sale.id, method=data.method, provider="CASH_REGISTER", transaction_reference=data.transaction_reference, status="APPROVED", amount=sale.total, paid_at=datetime.now(UTC))
    db.add(payment)
    db.flush()
    confirm_sale(db, sale, cashier)
    return get_sale(db, sale.id)


def initiate_electronic_payment(db: Session, data: ElectronicPaymentRequest) -> Payment:
    sale = get_sale(db, data.sale_id)
    if sale.channel != "DIGITAL" or sale.status != "PENDING":
        raise error("INVALID_ELECTRONIC_SALE", "La venta digital no está pendiente de pago.", status.HTTP_409_CONFLICT)
    existing = db.scalar(select(Payment).where(Payment.idempotency_key == data.idempotency_key))
    if existing is not None:
        return existing
    payment = Payment(sale_id=sale.id, method=data.method, provider="SANDBOX", transaction_reference=f"SANDBOX-{uuid4().hex.upper()}", status="PENDING", amount=sale.total, idempotency_key=data.idempotency_key)
    db.add(payment)
    db.flush()
    return payment


def process_electronic_notification(db: Session, data: ElectronicNotificationRequest) -> Payment:
    payment = db.scalar(select(Payment).where(Payment.transaction_reference == data.transaction_reference))
    if payment is None:
        raise error("PAYMENT_NOT_FOUND", "Pago no encontrado.", status.HTTP_404_NOT_FOUND)
    if payment.amount != data.amount:
        raise error("PAYMENT_AMOUNT_MISMATCH", "El monto notificado no coincide con la compra.", status.HTTP_409_CONFLICT)
    if payment.status == "APPROVED":
        return payment
    payment.status = data.status
    if data.status == "APPROVED":
        payment.paid_at = datetime.now(UTC)
        sale = get_sale(db, payment.sale_id)
        confirm_sale(db, sale, None)
    elif data.status in {"REJECTED", "CANCELLED"}:
        sale = get_sale(db, payment.sale_id)
        sale.status = "FAILED"
    db.flush()
    return payment
