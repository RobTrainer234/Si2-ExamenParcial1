from datetime import UTC, date, datetime
from decimal import Decimal
from math import ceil
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.audit import record_audit
from app.core.models import Branch, Cart, CartItem, Inventory, InventoryMovement, Payment, ProductVariant, Promotion, PromotionProduct, Sale, SaleItem, SaleShippingSnapshot, User
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


def _best_promotion_discount(db: Session, product_id: int, line_total: Decimal) -> Decimal:
    now = datetime.now(UTC)
    promotions = db.scalars(
        select(Promotion)
        .join(PromotionProduct, PromotionProduct.promotion_id == Promotion.id)
        .where(
            PromotionProduct.product_id == product_id,
            Promotion.is_active.is_(True),
            Promotion.starts_at <= now,
            Promotion.ends_at >= now,
        )
    ).all()
    discounts: list[Decimal] = []
    for promotion in promotions:
        if promotion.discount_type == "PERCENT":
            discounts.append((line_total * promotion.discount_value / Decimal("100")).quantize(Decimal("0.01")))
        elif promotion.discount_type == "FIXED":
            discounts.append(min(line_total, promotion.discount_value))
    return max(discounts) if discounts else Decimal("0")


def _line_promotion_discount(db: Session, variant_id: int, quantity: int, unit_price: Decimal) -> Decimal:
    variant = db.get(ProductVariant, variant_id)
    if variant is None:
        return Decimal("0")
    return _best_promotion_discount(db, variant.product_id, unit_price * quantity)


def serialize_cart(cart: Cart, db: Session) -> dict[str, object]:
    items = []
    for item in cart.items:
        variant = item.product_variant
        available = max(_available_any_branch(db, variant.id), 0)
        items.append({"id": item.id, "product_variant_id": variant.id, "product_id": variant.product_id, "product_name": variant.product.name, "sku": variant.sku, "size_name": variant.size.name, "color_name": variant.color.name, "quantity": item.quantity, "unit_price": item.unit_price, "line_total": item.unit_price * item.quantity, "available_quantity": available})
    subtotal = sum((item["line_total"] for item in items), Decimal("0"))
    discount = sum((_line_promotion_discount(db, item["product_variant_id"], item["quantity"], item["unit_price"]) for item in items), Decimal("0"))
    discount = min(discount, subtotal)
    return {"id": cart.id, "customer_id": cart.customer_id, "status": cart.status, "items": items, "subtotal": subtotal, "discount": discount, "total": subtotal - discount, "updated_at": cart.updated_at}


def _available_any_branch(db: Session, variant_id: int) -> int:
    return db.scalar(select(func.coalesce(func.sum(Inventory.stock_quantity - Inventory.reserved_quantity), 0)).where(Inventory.product_variant_id == variant_id)) or 0


def _validate_product_catalog_status(product) -> None:
    today = date.today()
    season = product.season
    collection = product.collection
    if season and (not season.is_active or (season.starts_on and season.starts_on > today) or (season.ends_on and season.ends_on < today)):
        raise error("PRODUCT_OUTSIDE_VALIDITY", "El producto no está vigente para venta.")
    if collection and not collection.is_active:
        raise error("PRODUCT_OUTSIDE_VALIDITY", "El producto no está vigente para venta.")


def add_cart_item(db: Session, customer_id: int, data: CartItemRequest) -> Cart:
    cart = get_cart(db, customer_id)
    variant = db.scalar(select(ProductVariant).options(joinedload(ProductVariant.product)).where(ProductVariant.id == data.product_variant_id, ProductVariant.is_active.is_(True)))
    if variant is None or not variant.product.is_active:
        raise error("VARIANT_NOT_FOUND_OR_INACTIVE", "La variante no existe o está inactiva.")
    _validate_product_catalog_status(variant.product)
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
        joinedload(Sale.shipping_snapshot),
    )


def get_sale(db: Session, sale_id: int) -> Sale:
    sale = db.execute(sale_query().where(Sale.id == sale_id)).unique().scalar_one_or_none()
    if sale is None:
        raise error("SALE_NOT_FOUND", "Venta no encontrada.", status.HTTP_404_NOT_FOUND)
    return sale


def list_customer_purchases(db: Session, customer_id: int, page: int, page_size: int) -> dict[str, object]:
    total = db.scalar(select(func.count(Sale.id)).where(Sale.customer_id == customer_id)) or 0
    sales = db.execute(sale_query().where(Sale.customer_id == customer_id).order_by(Sale.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).unique().scalars().all()
    return {"items": [serialize_sale(sale) for sale in sales], "page": page, "page_size": page_size, "total": total, "total_pages": ceil(total / page_size) if total else 0}


def get_customer_purchase(db: Session, customer_id: int, sale_id: int) -> Sale:
    sale = get_sale(db, sale_id)
    if sale.customer_id != customer_id:
        raise error("PURCHASE_NOT_FOUND", "Compra no encontrada.", status.HTTP_404_NOT_FOUND)
    return sale


def serialize_shipping_snapshot(snapshot: SaleShippingSnapshot | None) -> dict[str, object] | None:
    if snapshot is None:
        return None
    return {
        "recipient_name": snapshot.recipient_name,
        "recipient_ci": snapshot.recipient_ci,
        "recipient_phone": snapshot.recipient_phone,
        "department_or_city": snapshot.department_or_city,
        "zone": snapshot.zone,
        "street": snapshot.street,
        "house_number": snapshot.house_number,
        "reference": snapshot.reference,
    }


def serialize_sale(sale: Sale) -> dict[str, object]:
    return {"id": sale.id, "order_number": sale.order_number, "customer_id": sale.customer_id, "branch_id": sale.branch_id, "cashier_id": sale.cashier_id, "channel": sale.channel, "status": sale.status, "fulfillment_type": sale.fulfillment_type, "shipping_details": serialize_shipping_snapshot(sale.shipping_snapshot), "subtotal": sale.subtotal, "discount": sale.discount, "total": sale.total, "created_at": sale.created_at, "items": [{"id": item.id, "product_variant_id": item.product_variant_id, "product_name": item.product_variant.product.name, "sku": item.product_variant.sku, "quantity": item.quantity, "unit_price": item.unit_price, "discount": item.discount, "line_total": item.line_total} for item in sale.items], "payments": [serialize_payment(payment) for payment in sale.payments]}


def serialize_payment(payment: Payment) -> dict[str, object]:
    return {"id": payment.id, "sale_id": payment.sale_id, "method": payment.method, "provider": payment.provider, "transaction_reference": payment.transaction_reference, "status": payment.status, "amount": payment.amount, "received_amount": payment.received_amount, "change_amount": payment.change_amount, "paid_at": payment.paid_at}


def _validate_branch(db: Session, branch_id: int) -> Branch:
    branch = db.scalar(select(Branch).where(Branch.id == branch_id, Branch.is_active.is_(True)))
    if branch is None:
        raise error("BRANCH_NOT_FOUND_OR_INACTIVE", "La sucursal no existe o está inactiva.")
    return branch


def _variant(db: Session, variant_id: int) -> ProductVariant:
    variant = db.scalar(select(ProductVariant).options(joinedload(ProductVariant.product)).where(ProductVariant.id == variant_id, ProductVariant.is_active.is_(True)))
    if variant is None or not variant.product.is_active:
        raise error("VARIANT_NOT_FOUND_OR_INACTIVE", "Una variante no existe o está inactiva.")
    _validate_product_catalog_status(variant.product)
    return variant


def _new_order_number() -> str:
    return f"FS-{datetime.now(UTC):%Y%m%d}-{uuid4().hex[:8].upper()}"


def _create_sale(
    db: Session,
    branch_id: int,
    channel: str,
    customer_id: int | None,
    cashier_id: int | None,
    items: list[tuple[int, int, Decimal]],
    discount: Decimal,
    fulfillment_type: str = "PICKUP",
    shipping_details: dict[str, str] | None = None,
) -> Sale:
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
        gross_line_total = unit_price * quantity
        promotion_discount = _line_promotion_discount(db, variant_id, quantity, unit_price)
        line_discount = min(gross_line_total, promotion_discount)
        subtotal += gross_line_total
        sale_items.append(SaleItem(product_variant_id=variant_id, quantity=quantity, unit_price=unit_price, discount=line_discount, line_total=gross_line_total - line_discount))
    promotion_discount_total = sum((item.discount for item in sale_items), Decimal("0"))
    total_discount = discount + promotion_discount_total
    if total_discount > subtotal:
        raise error("INVALID_DISCOUNT", "El descuento no puede superar el subtotal.")
    if fulfillment_type not in {"PICKUP", "DELIVERY"}:
        raise error("INVALID_FULFILLMENT_TYPE", "El tipo de entrega no es válido.")
    if fulfillment_type == "DELIVERY" and shipping_details is None:
        raise error("SHIPPING_DETAILS_REQUIRED", "Los datos de envío son obligatorios para delivery.")
    sale = Sale(order_number=_new_order_number(), customer_id=customer_id, branch_id=branch_id, cashier_id=cashier_id, channel=channel, status="PENDING", fulfillment_type=fulfillment_type, subtotal=subtotal, discount=total_discount, total=subtotal - total_discount, items=sale_items)
    if fulfillment_type == "DELIVERY" and shipping_details is not None:
        sale.shipping_snapshot = SaleShippingSnapshot(**shipping_details)
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
    shipping_details = data.shipping_details.model_dump() if data.shipping_details is not None else None
    return _create_sale(db, data.branch_id, "DIGITAL", customer.id, None, items, data.discount, data.fulfillment_type, shipping_details)


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
        movement = InventoryMovement(inventory_id=locked.id, movement_type="SALE", quantity=item.quantity, stock_before=before, stock_after=locked.stock_quantity, reason="Venta confirmada", reference_type="sale", reference_id=sale.id, created_by=user.id if user else None)
        db.add(movement)
        db.flush()
        record_audit(db, user, "CREATE", "inventory_movement", movement.id, "Salida de inventario por venta.", new_values={"inventory_id": locked.id, "movement_type": "SALE", "quantity": item.quantity, "stock_before": before, "stock_after": locked.stock_quantity, "reference_type": "sale", "reference_id": sale.id})


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
    if data.method != "CASH" and data.amount != sale.total:
        raise error("PAYMENT_AMOUNT_MISMATCH", "Para tarjeta o QR el monto debe coincidir exactamente con el total.", status.HTTP_400_BAD_REQUEST)
    if data.method != "CASH" and not data.transaction_reference:
        raise error("PAYMENT_REFERENCE_REQUIRED", "La referencia es obligatoria para tarjeta o QR.", status.HTTP_400_BAD_REQUEST)
    change_amount = data.amount - sale.total if data.method == "CASH" else Decimal("0")
    payment = Payment(sale_id=sale.id, method=data.method, provider="CASH_REGISTER", transaction_reference=data.transaction_reference, status="APPROVED", amount=sale.total, received_amount=data.amount, change_amount=change_amount, paid_at=datetime.now(UTC))
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
        if existing.sale_id != data.sale_id:
            raise error("IDEMPOTENCY_KEY_CONFLICT", "La clave de idempotencia ya fue usada para otra venta.", status.HTTP_409_CONFLICT)
        if existing.method != data.method:
            raise error("IDEMPOTENCY_KEY_CONFLICT", "La clave de idempotencia ya fue usada con otro método de pago.", status.HTTP_409_CONFLICT)
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
    if payment.status in {"REJECTED", "CANCELLED"}:
        raise error("PAYMENT_TERMINAL_STATE", "El pago ya se encuentra en un estado terminal.", status.HTTP_409_CONFLICT)
    payment.status = data.status
    if data.status == "APPROVED":
        payment.paid_at = datetime.now(UTC)
        sale = get_sale(db, payment.sale_id)
        confirm_sale(db, sale, None)
        if sale.customer_id is not None:
            cart = get_cart(db, sale.customer_id)
            cart.items.clear()
            db.flush()
    elif data.status in {"REJECTED", "CANCELLED"}:
        sale = get_sale(db, payment.sale_id)
        sale.status = "FAILED"
    db.flush()
    return payment


def process_sale_return(db: Session, sale_id: int, reason: str, user: User) -> Sale:
    sale = get_sale(db, sale_id)
    if sale.status != "CONFIRMED":
        raise error("INVALID_SALE_STATE_FOR_RETURN", f"Solo se pueden devolver ventas en estado CONFIRMED. Estado actual: {sale.status}", status.HTTP_409_CONFLICT)
    clean_reason = reason.strip()
    if len(clean_reason) < 3:
        raise error("INVALID_RETURN_REASON", "El motivo de la devolución debe contener al menos 3 caracteres.", status.HTTP_400_BAD_REQUEST)
    
    old_status = sale.status
    sale.status = "RETURNED"

    # Reintegrar existencias al inventario de la sucursal
    for item in sale.items:
        inventory_id = db.scalar(select(Inventory.id).where(Inventory.branch_id == sale.branch_id, Inventory.product_variant_id == item.product_variant_id))
        if inventory_id is not None:
            locked = get_locked_inventory(db, inventory_id)
            before = locked.stock_quantity
            locked.stock_quantity += item.quantity
            movement = InventoryMovement(
                inventory_id=locked.id,
                movement_type="RETURN",
                quantity=item.quantity,
                stock_before=before,
                stock_after=locked.stock_quantity,
                reason=f"Devolución de venta {sale.order_number}: {clean_reason}",
                reference_type="sale_return",
                reference_id=sale.id,
                created_by=user.id,
            )
            db.add(movement)
            db.flush()
            record_audit(
                db,
                user,
                "CREATE",
                "inventory_movement",
                movement.id,
                "Reintegro de inventario por devolución de venta.",
                new_values={
                    "inventory_id": locked.id,
                    "movement_type": "RETURN",
                    "quantity": item.quantity,
                    "stock_before": before,
                    "stock_after": locked.stock_quantity,
                    "reference_type": "sale_return",
                    "reference_id": sale.id,
                },
            )

    record_audit(
        db,
        user,
        "UPDATE",
        "sale",
        sale.id,
        f"Venta {sale.order_number} devuelta. Motivo: {clean_reason}",
        old_values={"status": old_status},
        new_values={"status": "RETURNED", "reason": clean_reason},
    )
    db.flush()
    return get_sale(db, sale.id)

