from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
import hashlib
import hmac
import json
from math import ceil
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.audit import record_audit
from app.core.config import settings
from app.core.models import Branch, Cart, CartItem, CreditNoteRedemption, Devolucion, DetalleDevolucion, GarmentExchange, GarmentExchangeItem, Inventory, InventoryMovement, InventoryQuarantine, Payment, Product, ProductVariant, Promotion, PromotionProduct, Sale, SaleItem, SaleShippingSnapshot, User
from app.modules.commerce.schemas import (
    CartItemRequest,
    CartItemUpdateRequest,
    CashPaymentRequest,
    CreditNoteLookupRequest,
    DigitalPurchaseRequest,
    ElectronicNotificationRequest,
    ElectronicPaymentRequest,
    ExchangeQuoteRequest,
    ItemExchangeRequest,
    PhysicalSaleRequest,
    SaleReturnRequest,
)
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
    variant = db.scalar(select(ProductVariant).where(ProductVariant.id == variant_id))
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


def _settlement_response(db: Session, sale_id: int, redemption: CreditNoteRedemption) -> dict[str, object]:
    sale = db.execute(sale_query().where(Sale.id == sale_id).execution_options(populate_existing=True)).unique().scalar_one()
    tender = next((payment for payment in sale.payments if payment.method in {"CASH", "CARD", "QR"}), None)
    return {**serialize_sale(sale), "redemption_id": redemption.id, "applied_amount": redemption.applied_amount, "post_redemption_balance": redemption.post_redemption_balance, "cash_change": tender.change_amount if tender and tender.method == "CASH" else Decimal("0.00")}


def _credit_note_payment_idempotency_key(*, tenant_id: int, credit_note_id: int, sale_id: int, request_idempotency_key: str) -> str:
    scope = json.dumps(
        {"tenant_id": tenant_id, "credit_note_id": credit_note_id, "sale_id": sale_id, "request_idempotency_key": request_idempotency_key},
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"CN-{hashlib.sha256(scope.encode()).hexdigest()}"


def lookup_credit_note(db: Session, data: CreditNoteLookupRequest, cashier: User) -> dict[str, object]:
    note = db.scalar(
        select(Devolucion).where(
            Devolucion.tenant_id == cashier.tenant_id,
            Devolucion.codigo_nota_credito == data.credit_note_code,
            Devolucion.tipo_reembolso == "NOTA_CREDITO",
            Devolucion.estado == "COMPLETADA",
        )
    )
    beneficiary = None
    if note is not None:
        beneficiary = db.scalar(
            select(User).where(
                User.id == note.beneficiario_id,
                User.tenant_id == cashier.tenant_id,
                User.is_active.is_(True),
                User.role.has(code="CLIENT"),
            )
        )
    if note is None or beneficiary is None or note.beneficiario_id != data.customer_id:
        raise error("INVALID_CREDIT_NOTE_LOOKUP", "La nota de crédito no está disponible para este cliente.")
    balance = note.saldo_nota_credito if note.saldo_nota_credito is not None else note.total_devuelto
    balance = max(balance, Decimal("0.00"))
    if balance <= 0:
        raise error("EXHAUSTED_CREDIT_NOTE", "La nota de crédito no tiene saldo disponible.", status.HTTP_409_CONFLICT)
    return {"available_balance": balance, "customer_id": beneficiary.id, "expires_at": None}


def settle_credit_note(db: Session, sale_id: int, data, cashier: User) -> dict[str, object]:
    canonical = {"sale_id": sale_id, "credit_note_code": data.credit_note_code, "method": data.method, "amount": str(data.amount) if data.amount is not None else None, "transaction_reference": data.transaction_reference}
    fingerprint = hashlib.sha256(json.dumps({"tenant_id": cashier.tenant_id, "body": canonical}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    existing = db.scalar(select(CreditNoteRedemption).where(CreditNoteRedemption.tenant_id == cashier.tenant_id, CreditNoteRedemption.idempotency_key == data.idempotency_key))
    if existing is not None:
        if existing.request_fingerprint != fingerprint or existing.sale_id != sale_id:
            raise error("IDEMPOTENCY_KEY_CONFLICT", "La clave de idempotencia ya fue usada con otra solicitud.", status.HTTP_409_CONFLICT)
        return _settlement_response(db, sale_id, existing)
    sale = db.scalar(select(Sale).where(Sale.id == sale_id, Sale.tenant_id == cashier.tenant_id).with_for_update())
    if sale is None:
        raise error("SALE_NOT_FOUND", "Venta no encontrada.", status.HTTP_404_NOT_FOUND)
    if sale.channel != "PHYSICAL" or sale.status != "PENDING":
        raise error("INVALID_CREDIT_NOTE_SALE", "Solo se puede liquidar una venta presencial pendiente.", status.HTTP_409_CONFLICT)
    note = db.scalar(select(Devolucion).where(Devolucion.tenant_id == cashier.tenant_id, Devolucion.codigo_nota_credito == data.credit_note_code).with_for_update())
    if note is None:
        raise error("INVALID_CREDIT_NOTE", "La nota de crédito no es válida para esta venta.", status.HTTP_400_BAD_REQUEST)
    existing = db.scalar(select(CreditNoteRedemption).where(CreditNoteRedemption.tenant_id == cashier.tenant_id, CreditNoteRedemption.idempotency_key == data.idempotency_key))
    if existing is not None:
        if existing.request_fingerprint != fingerprint or existing.sale_id != sale_id:
            raise error("IDEMPOTENCY_KEY_CONFLICT", "La clave de idempotencia ya fue usada con otra solicitud.", status.HTTP_409_CONFLICT)
        return _settlement_response(db, sale_id, existing)
    beneficiary = db.scalar(select(User).where(User.id == note.beneficiario_id, User.tenant_id == cashier.tenant_id, User.is_active.is_(True), User.role.has(code="CLIENT")))
    if beneficiary is None or note.tipo_reembolso != "NOTA_CREDITO" or note.estado != "COMPLETADA" or note.beneficiario_id != sale.customer_id:
        raise error("INVALID_CREDIT_NOTE", "La nota de crédito no es válida para esta venta.", status.HTTP_400_BAD_REQUEST)
    if note.venta_id == sale.id:
        raise error("CREDIT_NOTE_ORIGINAL_SALE", "La nota no puede aplicarse a la venta original.", status.HTTP_409_CONFLICT)
    if note.saldo_nota_credito is None:
        note.saldo_nota_credito = note.total_devuelto
    if note.saldo_nota_credito <= 0:
        raise error("EXHAUSTED_CREDIT_NOTE", "La nota de crédito no tiene saldo disponible.", status.HTTP_409_CONFLICT)
    applied = min(note.saldo_nota_credito, sale.total)
    remainder = sale.total - applied
    if remainder > 0:
        if data.method is None or data.amount is None:
            raise error("TENDER_REQUIRED", "Se requiere un medio de pago por el saldo restante.", status.HTTP_400_BAD_REQUEST)
        if data.amount < remainder:
            raise error("INSUFFICIENT_PAYMENT", "El monto recibido no cubre el saldo restante.", status.HTTP_400_BAD_REQUEST)
        if data.method != "CASH" and data.amount != remainder:
            raise error("PAYMENT_AMOUNT_MISMATCH", "Para tarjeta o QR el monto debe coincidir exactamente con el saldo.", status.HTTP_400_BAD_REQUEST)
        if data.method != "CASH" and not data.transaction_reference:
            raise error("PAYMENT_REFERENCE_REQUIRED", "La referencia es obligatoria para tarjeta o QR.", status.HTTP_400_BAD_REQUEST)
    elif any(value is not None for value in (data.method, data.amount, data.transaction_reference)):
        raise error("UNEXPECTED_TENDER", "No se requiere un medio de pago adicional.", status.HTTP_400_BAD_REQUEST)
    post_balance = note.saldo_nota_credito - applied
    payment_key = _credit_note_payment_idempotency_key(tenant_id=cashier.tenant_id, credit_note_id=note.id, sale_id=sale.id, request_idempotency_key=data.idempotency_key)
    credit_payment = Payment(tenant_id=cashier.tenant_id, sale_id=sale.id, method="CREDIT_NOTE", provider="CREDIT_NOTE", transaction_reference=f"CN-{hashlib.sha256(f'{note.id}:{sale.id}:{data.idempotency_key}'.encode()).hexdigest()}", status="APPROVED", amount=applied, received_amount=applied, change_amount=Decimal("0.00"), idempotency_key=payment_key, paid_at=datetime.now(UTC))
    db.add(credit_payment)
    db.flush()
    redemption = CreditNoteRedemption(tenant_id=cashier.tenant_id, credit_note_id=note.id, sale_id=sale.id, cashier_id=cashier.id, payment_id=credit_payment.id, idempotency_key=data.idempotency_key, request_fingerprint=fingerprint, applied_amount=applied, post_redemption_balance=post_balance)
    db.add(redemption)
    try:
        db.flush()
    except IntegrityError as exc:
        if "uq_credit_note_redemptions_tenant_key" not in str(exc):
            raise
        db.rollback()
        winner = db.scalar(select(CreditNoteRedemption).where(CreditNoteRedemption.tenant_id == cashier.tenant_id, CreditNoteRedemption.idempotency_key == data.idempotency_key))
        if winner is None:
            raise
        if winner.request_fingerprint != fingerprint or winner.sale_id != sale_id:
            raise error("IDEMPOTENCY_KEY_CONFLICT", "La clave de idempotencia ya fue usada con otra solicitud.", status.HTTP_409_CONFLICT)
        return _settlement_response(db, sale_id, winner)
    note.saldo_nota_credito = post_balance
    if remainder > 0:
        tender_payment = Payment(tenant_id=cashier.tenant_id, sale_id=sale.id, method=data.method, provider="CASH_REGISTER", transaction_reference=data.transaction_reference, status="APPROVED", amount=remainder, received_amount=data.amount, change_amount=data.amount - remainder if data.method == "CASH" else Decimal("0.00"), idempotency_key=f"CT-{hashlib.sha256(data.idempotency_key.encode()).hexdigest()}", paid_at=datetime.now(UTC))
        db.add(tender_payment)
        db.flush()
    confirm_sale(db, sale, cashier)
    return _settlement_response(db, sale.id, redemption)


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


def process_sale_return(db: Session, sale_id: int, data: SaleReturnRequest, user: User) -> Sale:
    sale = db.execute(sale_query().where(Sale.id == sale_id, Sale.tenant_id == user.tenant_id).with_for_update()).unique().scalar_one_or_none()
    if sale is None:
        raise error("SALE_NOT_FOUND", "Venta no encontrada.", status.HTTP_404_NOT_FOUND)
    if sale.status not in {"CONFIRMED", "RETURNED"}:
        raise error("INVALID_SALE_STATE_FOR_RETURN", "La venta no está habilitada para devolución.", status.HTTP_409_CONFLICT)
    clean_reason = data.reason.strip()
    payload = data.model_dump(mode="json")
    canonical_request = {"tenant_id": user.tenant_id, "sale_id": sale.id, "body": payload}
    fingerprint = hashlib.sha256(json.dumps(canonical_request, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    existing = db.scalar(select(Devolucion).where(Devolucion.tenant_id == user.tenant_id, Devolucion.idempotency_key == data.idempotency_key))
    if existing is not None:
        if existing.request_fingerprint != fingerprint:
            raise error("RETURN_IDEMPOTENCY_CONFLICT", "La clave de idempotencia ya fue usada con otra solicitud.", status.HTTP_409_CONFLICT)
        return get_sale(db, sale.id)
    if sale.branch_id is None:
        raise error("RETURN_BRANCH_REQUIRED", "La venta no tiene una sucursal válida para devolución.", status.HTTP_409_CONFLICT)
    branch = db.scalar(select(Branch).where(Branch.id == sale.branch_id, Branch.tenant_id == user.tenant_id, Branch.is_active.is_(True)))
    if branch is None:
        raise error("RETURN_BRANCH_NOT_FOUND_OR_INACTIVE", "La sucursal original no existe o está inactiva.", status.HTTP_409_CONFLICT)
    beneficiary_id = sale.customer_id or data.beneficiary_customer_id
    beneficiary = db.scalar(select(User).where(User.id == beneficiary_id, User.tenant_id == user.tenant_id, User.is_active.is_(True), User.role.has(code="CLIENT"))) if beneficiary_id else None
    if beneficiary is None:
        raise error("RETURN_BENEFICIARY_REQUIRED", "La devolución requiere un cliente beneficiario de la misma empresa.")
    if sale.customer_id is not None and data.beneficiary_customer_id not in {None, sale.customer_id}:
        raise error("RETURN_BENEFICIARY_MISMATCH", "El beneficiario debe ser el cliente de la venta.")

    requested = data.items or [{"sale_item_id": item.id, "quantity": item.quantity, "condition": "SELLABLE"} for item in sale.items]
    returned_by_item = dict(db.execute(select(DetalleDevolucion.detalle_venta_id, func.coalesce(func.sum(DetalleDevolucion.cantidad), 0)).join(Devolucion).where(Devolucion.venta_id == sale.id).group_by(DetalleDevolucion.detalle_venta_id)).all())
    sale_items = {item.id: item for item in sale.items}
    total = Decimal("0.00")
    details = []
    for line in requested:
        line_data = line if isinstance(line, dict) else line.model_dump()
        item = sale_items.get(line_data["sale_item_id"])
        if item is None or line_data["quantity"] + returned_by_item.get(item.id, 0) > item.quantity:
            raise error("RETURN_QUANTITY_EXCEEDED", "La cantidad devuelta supera la cantidad comprada o ya devuelta.", status.HTTP_409_CONFLICT)
        previous_subtotal = sum((detail.subtotal for detail in db.scalars(select(DetalleDevolucion).where(DetalleDevolucion.detalle_venta_id == item.id)).all()), Decimal("0.00"))
        returned_quantity = returned_by_item.get(item.id, 0)
        if returned_quantity + line_data["quantity"] == item.quantity:
            subtotal = item.line_total - previous_subtotal
        else:
            subtotal = (item.line_total * line_data["quantity"] / item.quantity).quantize(Decimal("0.01"))
        total += subtotal
        details.append((item, line_data["quantity"], line_data["condition"], subtotal))

    note_code = f"NC-{uuid4().hex[:10].upper()}"
    ledger = Devolucion(tenant_id=user.tenant_id, sucursal_id=sale.branch_id, venta_id=sale.id, cajero_id=user.id, numero_devolucion=f"DEV-{uuid4().hex[:10].upper()}", total_devuelto=total, saldo_nota_credito=total, tipo_reembolso="NOTA_CREDITO", codigo_nota_credito=note_code, beneficiario_id=beneficiary.id, idempotency_key=data.idempotency_key, request_fingerprint=fingerprint, motivo=clean_reason, estado="COMPLETADA")
    db.add(ledger)
    try:
        db.flush()
    except IntegrityError as exc:
        if "uq_devoluciones_tenant_idempotency_key" not in str(exc.orig or exc):
            raise
        db.rollback()
        winner = db.scalar(select(Devolucion).where(Devolucion.tenant_id == user.tenant_id, Devolucion.idempotency_key == data.idempotency_key))
        if winner is None:
            raise
        if winner.request_fingerprint != fingerprint:
            raise error("RETURN_IDEMPOTENCY_CONFLICT", "La clave de idempotencia ya fue usada con otra solicitud.", status.HTTP_409_CONFLICT)
        return get_sale(db, sale.id)
    for item, quantity, condition, subtotal in details:
        db.add(DetalleDevolucion(devolucion_id=ledger.id, detalle_venta_id=item.id, variante_producto_id=item.product_variant_id, cantidad=quantity, precio_unitario=item.unit_price, subtotal=subtotal, estado_prenda=condition, reintegrado_inventario=False))
        inventory_id = db.scalar(select(Inventory.id).where(Inventory.tenant_id == user.tenant_id, Inventory.branch_id == sale.branch_id, Inventory.product_variant_id == item.product_variant_id))
        if inventory_id is None:
            raise error("RETURN_INVENTORY_NOT_FOUND", "No existe inventario para registrar la devolución.", status.HTTP_409_CONFLICT)
        locked = get_locked_inventory(db, inventory_id)
        before = locked.stock_quantity
        db.add(InventoryMovement(tenant_id=user.tenant_id, inventory_id=locked.id, movement_type="RETURN", quantity=quantity, stock_before=before, stock_after=before, reason=f"Ingreso para inspección: {clean_reason}", reference_type="sale_return", reference_id=ledger.id, created_by=user.id))
        if condition == "SELLABLE":
            locked.stock_quantity += quantity
            db.add(InventoryMovement(tenant_id=user.tenant_id, inventory_id=locked.id, movement_type="RESTOCK", quantity=quantity, stock_before=before, stock_after=locked.stock_quantity, reason=f"Reingreso vendible de devolución {ledger.numero_devolucion}", reference_type="sale_return", reference_id=ledger.id, created_by=user.id))
    all_returned = all(returned_by_item.get(item.id, 0) + next((q for i, q, _, _ in details if i.id == item.id), 0) == item.quantity for item in sale.items)
    if all_returned:
        sale.status = "RETURNED"
    db.flush()
    return get_sale(db, sale.id)


_EXCHANGE_ELIGIBLE_STATUSES = ("COMPLETED", "CONFIRMED", "PENDING_DELIVERY", "DELIVERED")
_EXCHANGE_QUOTE_TTL = timedelta(minutes=5)


def _exchange_branch_ids(current_user: User) -> set[int] | None:
    if current_user.role.code == "ADMIN":
        return None
    return {branch.id for branch in current_user.branches}


def _get_store_exchange_policy_days(branch: Branch | None, tenant_id: int | None = None) -> int:
    """Retorna los días configurados de la política general de la sucursal/tienda."""
    if branch and hasattr(branch, "return_days") and branch.return_days:
        return branch.return_days
    return 30


def _resolve_product_exchange_policy(product: Product | None, store_default_days: int = 30) -> tuple[int, str]:
    """Determina los días de cambio permitidos y la nota de política según el tipo de prenda.
    Retorna: (dias_permitidos, nota_politica)
    - Prendas íntimas / Lencería / Baño: 0 días (no sujeta a cambio por norma sanitaria/higiene).
    - Vestidos de fiesta / Gala / Noche / Alta Costura: 15 días.
    - Prendas en liquidación / Outlet / Final Sale: 7 días.
    - Prendas generales / Casuales: store_default_days (ej. 30 días o configurado en tienda).
    """
    if product is None:
        return store_default_days, f"Política estándar: {store_default_days} días"
    category_name = (product.category.name if getattr(product, "category", None) else "").lower()
    prod_name = (product.name or "").lower()
    combined = f"{category_name} {prod_name}"

    if any(k in combined for k in ("interior", "lencer", "íntim", "intim", "bikini", "bañador", "calcet", "media")):
        return 0, "Prenda íntima: no sujeta a cambio ni devolución por norma sanitaria y de higiene"
    if any(k in combined for k in ("gala", "fiesta", "noche", "novia", "alta costura", "evento")):
        return 15, "Prenda de fiesta/gala: plazo especial de 15 días calendario"
    if any(k in combined for k in ("outlet", "liquidac", "final sale", "descuento especial")):
        return 7, "Prenda en liquidación: plazo promocional de 7 días calendario"
    return store_default_days, f"Política de tienda: {store_default_days} días para prendas generales"


def _load_exchange_sale(db: Session, order_number: str, current_user: User) -> Sale:
    query = select(Sale).where(
        Sale.tenant_id == current_user.tenant_id,
        Sale.order_number == order_number,
    )
    branch_ids = _exchange_branch_ids(current_user)
    if branch_ids is not None:
        query = query.where(Sale.branch_id.in_(branch_ids))
    sale = db.execute(query.options(joinedload(Sale.items).joinedload(SaleItem.product_variant).joinedload(ProductVariant.product).joinedload(Product.category), joinedload(Sale.payments))).unique().scalar_one_or_none()
    if sale is None:
        raise error("SALE_NOT_FOUND", "Venta no encontrada.", status.HTTP_404_NOT_FOUND)
    _validate_exchange_sale_eligibility(sale)
    return sale


def _validate_exchange_sale_eligibility(sale: Sale) -> None:
    if sale.status not in _EXCHANGE_ELIGIBLE_STATUSES:
        raise error("SALE_NOT_ELIGIBLE_FOR_EXCHANGE", "La venta no es elegible para cambios.", status.HTTP_400_BAD_REQUEST)
    sale_created = sale.created_at.replace(tzinfo=UTC) if sale.created_at.tzinfo is None else sale.created_at
    if datetime.now(UTC) > sale_created + timedelta(days=90):
        raise error("EXCHANGE_WINDOW_EXPIRED", "El comprobante supera el plazo máximo general de la tienda (90 días).", status.HTTP_400_BAD_REQUEST)


def _quote_binding(*, current_user: User, sale: Sale, sale_item: SaleItem, returned_quantity: int, new_variant_id: int, new_quantity: int, consumed: int, replacement_price: Decimal, available_stock: int, reserved_stock: int, cash_settlement_eligible: bool, quote_expires_at: datetime) -> dict[str, object]:
    return {
        "tenant_id": current_user.tenant_id,
        "branch_id": sale.branch_id,
        "sale_id": sale.id,
        "sale_item_id": sale_item.id,
        "source_variant_id": sale_item.product_variant_id,
        "returned_quantity": returned_quantity,
        "purchased_quantity": sale_item.quantity,
        "consumed_exchange_quantity": consumed,
        "source_paid_line_total": str(sale_item.line_total),
        "replacement_variant_id": new_variant_id,
        "replacement_quantity": new_quantity,
        "replacement_catalog_price": str(replacement_price),
        "available_stock": available_stock,
        "reserved_stock": reserved_stock,
        "cash_settlement_eligible": cash_settlement_eligible,
        "quote_expires_at": quote_expires_at.isoformat(),
    }


def _sign_quote(binding: dict[str, object]) -> str:
    encoded = json.dumps(binding, sort_keys=True, separators=(",", ":")).encode()
    return hmac.new(settings.jwt_secret.encode(), encoded, hashlib.sha256).hexdigest()


def _exchange_context(db: Session, sale: Sale, data: ExchangeQuoteRequest, current_user: User, *, lock: bool = False) -> tuple[SaleItem, ProductVariant, ProductVariant, int, Inventory, bool]:
    items_query = select(SaleItem).where(SaleItem.sale_id == sale.id)
    if lock:
        items_query = items_query.with_for_update()
    items = db.scalars(items_query).all()
    matching_item = next((item for item in items if item.product_variant_id == data.returned_variant_id), None)
    consumed = db.scalar(select(func.coalesce(func.sum(GarmentExchangeItem.returned_quantity), 0)).join(GarmentExchange).where(GarmentExchange.sale_id == sale.id, GarmentExchangeItem.sale_item_id == (matching_item.id if matching_item else -1))) or 0
    source_variant = db.scalar(select(ProductVariant).options(joinedload(ProductVariant.product)).where(ProductVariant.id == data.returned_variant_id, ProductVariant.is_active.is_(True)))
    replacement_variant = db.scalar(select(ProductVariant).options(joinedload(ProductVariant.product)).where(ProductVariant.id == data.new_variant_id, ProductVariant.is_active.is_(True)))
    if matching_item is None or matching_item.quantity - consumed < data.returned_quantity:
        raise error("ITEM_ALREADY_EXCHANGED", "La cantidad solicitada ya fue cambiada previamente.", status.HTTP_409_CONFLICT)
    if source_variant is None or replacement_variant is None or not source_variant.product.is_active or not replacement_variant.product.is_active:
        raise error("VARIANT_NOT_FOUND_OR_INACTIVE", "La variante de origen o reemplazo no existe o está inactiva.", status.HTTP_400_BAD_REQUEST)
    if source_variant.tenant_id != current_user.tenant_id or replacement_variant.tenant_id != current_user.tenant_id:
        raise error("VARIANT_NOT_FOUND_OR_INACTIVE", "Las variantes no pertenecen al tenant de la venta.", status.HTTP_403_FORBIDDEN)
    _validate_product_catalog_status(source_variant.product)
    _validate_product_catalog_status(replacement_variant.product)
    inv_query = select(Inventory).where(Inventory.tenant_id == current_user.tenant_id, Inventory.branch_id == sale.branch_id, Inventory.product_variant_id == data.new_variant_id)
    if lock:
        inv_query = inv_query.with_for_update()
    inventory = db.scalar(inv_query)
    if inventory is None:
        raise error("NEW_ITEM_INVENTORY_NOT_FOUND", "No existe inventario para la variante del cambio.", status.HTTP_409_CONFLICT)
    return matching_item, source_variant, replacement_variant, consumed, inventory, _is_cash_origin(sale.payments)


def lookup_return_sale(db: Session, order_number: str, current_user: User) -> dict[str, object]:
    query = select(Sale).where(Sale.tenant_id == current_user.tenant_id, Sale.order_number == order_number)
    branch_ids = _exchange_branch_ids(current_user)
    if branch_ids is not None:
        query = query.where(Sale.branch_id.in_(branch_ids))
    sale = db.execute(query.options(joinedload(Sale.items).joinedload(SaleItem.product_variant).joinedload(ProductVariant.product))).unique().scalar_one_or_none()
    if sale is None:
        raise error("SALE_NOT_FOUND", "Venta no encontrada.", status.HTTP_404_NOT_FOUND)
    if sale.status not in {"CONFIRMED", "RETURNED"}:
        raise error("INVALID_SALE_STATE_FOR_RETURN", "La venta no está habilitada para devolución.", status.HTTP_409_CONFLICT)
    returned = dict(db.execute(select(DetalleDevolucion.detalle_venta_id, func.coalesce(func.sum(DetalleDevolucion.cantidad), 0)).join(Devolucion).where(Devolucion.venta_id == sale.id).group_by(DetalleDevolucion.detalle_venta_id)).all())
    return {"sale_id": sale.id, "order_number": sale.order_number, "sale_date": sale.created_at, "branch_id": sale.branch_id, "status": sale.status, "customer_id": sale.customer_id, "items": [{"id": item.id, "variant_id": item.product_variant_id, "name": item.product_variant.product.name, "sku": item.product_variant.sku, "purchased_quantity": item.quantity, "net_paid_line_total": item.line_total, "remaining_returnable_quantity": max(item.quantity - returned.get(item.id, 0), 0)} for item in sale.items]}


def lookup_exchange_sale(db: Session, order_number: str, current_user: User) -> dict[str, object]:
    sale = _load_exchange_sale(db, order_number, current_user)
    consumed_by_item = dict(db.execute(select(GarmentExchangeItem.sale_item_id, func.coalesce(func.sum(GarmentExchangeItem.returned_quantity), 0)).join(GarmentExchange).where(GarmentExchange.sale_id == sale.id).group_by(GarmentExchangeItem.sale_item_id)).all())
    branch = db.scalar(select(Branch).where(Branch.id == sale.branch_id)) if sale.branch_id else None
    store_policy_days = _get_store_exchange_policy_days(branch, sale.tenant_id)
    sale_created = sale.created_at.replace(tzinfo=UTC) if sale.created_at.tzinfo is None else sale.created_at
    days_elapsed = max(0, (datetime.now(UTC) - sale_created).days)

    items_payload = []
    has_any_exchangeable = False
    for item in sale.items:
        product = item.product_variant.product if item.product_variant else None
        category_name = product.category.name if product and getattr(product, "category", None) else None
        exchange_days, policy_note = _resolve_product_exchange_policy(product, store_policy_days)
        remaining = max(item.quantity - consumed_by_item.get(item.id, 0), 0)
        is_exchangeable = (remaining > 0) and (exchange_days > 0) and (days_elapsed <= exchange_days)
        if is_exchangeable:
            has_any_exchangeable = True
        items_payload.append({
            "id": item.id,
            "variant_id": item.product_variant_id,
            "name": product.name if product else "Prenda",
            "sku": item.product_variant.sku if item.product_variant else "",
            "purchased_quantity": item.quantity,
            "net_paid_line_total": item.line_total,
            "remaining_exchangeable_quantity": remaining,
            "category_name": category_name,
            "exchange_days": exchange_days,
            "is_exchangeable": is_exchangeable,
            "policy_note": policy_note,
        })

    return {
        "sale_id": sale.id,
        "order_number": sale.order_number,
        "sale_date": sale.created_at,
        "branch_id": sale.branch_id,
        "status": sale.status,
        "store_policy_days": store_policy_days,
        "days_elapsed": days_elapsed,
        "is_within_policy": has_any_exchangeable,
        "policy_summary": f"Política de sucursal: {store_policy_days} días generales. Políticas por prenda aplicadas.",
        "items": items_payload,
    }


def create_exchange_quote(db: Session, sale_id: int, data: ExchangeQuoteRequest, current_user: User) -> dict[str, object]:
    sale = db.scalar(select(Sale).where(Sale.id == sale_id, Sale.tenant_id == current_user.tenant_id).options(joinedload(Sale.payments)))
    if sale is None or (_exchange_branch_ids(current_user) is not None and sale.branch_id not in _exchange_branch_ids(current_user)):
        raise error("SALE_NOT_FOUND", "Venta no encontrada.", status.HTTP_404_NOT_FOUND)
    _validate_exchange_sale_eligibility(sale)
    item, _, replacement, consumed, inventory, cash_eligible = _exchange_context(db, sale, data, current_user)
    branch = db.scalar(select(Branch).where(Branch.id == sale.branch_id)) if sale.branch_id else None
    store_days = _get_store_exchange_policy_days(branch, sale.tenant_id)
    item_days, item_policy_note = _resolve_product_exchange_policy(item.product_variant.product if item.product_variant else None, store_days)
    sale_created = sale.created_at.replace(tzinfo=UTC) if sale.created_at.tzinfo is None else sale.created_at
    days_elapsed = max(0, (datetime.now(UTC) - sale_created).days)
    if item_days == 0:
        raise error("ITEM_NOT_EXCHANGEABLE", "Esta prenda no está sujeta a cambio o devolución por norma sanitaria y de higiene.", status.HTTP_400_BAD_REQUEST)
    if days_elapsed > item_days:
        raise error("EXCHANGE_WINDOW_EXPIRED", f"El plazo de cambio para esta prenda ({item_days} días) ha expirado (han transcurrido {days_elapsed} días desde la compra).", status.HTTP_400_BAD_REQUEST)
    available = inventory.stock_quantity - inventory.reserved_quantity
    if available < data.new_quantity:
        raise error("INSUFFICIENT_STOCK", "Stock insuficiente para la nueva prenda solicitada.", status.HTTP_409_CONFLICT)
    returned_value = (item.line_total / item.quantity * data.returned_quantity).quantize(Decimal("0.01"))
    delivered_value = (replacement.product.price * data.new_quantity).quantize(Decimal("0.01"))
    difference = delivered_value - returned_value
    settlement_eligible = cash_eligible or difference == 0
    expires_at = datetime.now(UTC) + _EXCHANGE_QUOTE_TTL
    binding = _quote_binding(current_user=current_user, sale=sale, sale_item=item, returned_quantity=data.returned_quantity, new_variant_id=data.new_variant_id, new_quantity=data.new_quantity, consumed=consumed, replacement_price=replacement.product.price, available_stock=available, reserved_stock=inventory.reserved_quantity, cash_settlement_eligible=settlement_eligible, quote_expires_at=expires_at)
    return {"sale_id": sale.id, "sale_item_id": item.id, "returned_variant_id": data.returned_variant_id, "returned_quantity": data.returned_quantity, "new_variant_id": data.new_variant_id, "new_quantity": data.new_quantity, "returned_value": returned_value, "replacement_unit_price": replacement.product.price, "delivered_value": delivered_value, "difference": difference, "cash_settlement_eligible": settlement_eligible, "available_stock": available, "reserved_stock": inventory.reserved_quantity, "expires_at": expires_at, "quote_fingerprint": _sign_quote(binding)}


def _is_exchange_idempotency_violation(exc: IntegrityError) -> bool:
    original = getattr(exc, "orig", None)
    constraint_name = getattr(getattr(original, "diag", None), "constraint_name", None)
    if constraint_name == "uq_garment_exchanges_tenant_idempotency":
        return True
    return "uq_garment_exchanges_tenant_idempotency" in str(original or exc)


def _flush_exchange_or_replay(db: Session, exchange: GarmentExchange, fingerprint: str) -> dict[str, Any] | None:
    try:
        db.flush()
    except IntegrityError as exc:
        if not _is_exchange_idempotency_violation(exc):
            raise
        db.rollback()
        winner = db.scalar(select(GarmentExchange).where(GarmentExchange.tenant_id == exchange.tenant_id, GarmentExchange.idempotency_key == exchange.idempotency_key))
        if winner is None:
            raise
        if winner.request_fingerprint != fingerprint:
            raise error("IDEMPOTENCY_KEY_CONFLICT", "La clave de idempotencia ya fue usada con otra solicitud.", status.HTTP_409_CONFLICT)
        return winner.result_json
    return None


def _is_cash_origin(payments: list[Payment]) -> bool:
    return bool(payments) and all(
        payment.method == "CASH" and payment.status in {"APPROVED", "SETTLED"}
        for payment in payments
    )


def _exchange_cash_settlement(difference: Decimal, cash_tendered: Decimal | None) -> dict[str, Decimal | bool | None]:
    if difference > 0:
        return {
            "cash_tendered": cash_tendered,
            "cash_change": (cash_tendered - difference).quantize(Decimal("0.01")) if cash_tendered is not None else None,
            "cash_refunded": None,
            "create_payment": True,
        }
    if difference < 0:
        return {
            "cash_tendered": None,
            "cash_change": None,
            "cash_refunded": abs(difference).quantize(Decimal("0.01")),
            "create_payment": False,
        }
    return {"cash_tendered": None, "cash_change": None, "cash_refunded": None, "create_payment": False}


def create_exchange_quarantine(
    db: Session,
    exchange_item: GarmentExchangeItem,
    inventory: Inventory,
    user: User,
    condition: str = "EXCELLENT",
    checklist: list[str] | None = None,
    notes: str | None = None,
) -> InventoryQuarantine:
    chk_str = ", ".join(checklist) if checklist else "Inspección estándar conforme"
    reason_str = f"Condición: {condition} | Inspección: {chk_str}"
    if notes:
        reason_str += f" | Obs: {notes}"
    quarantine = InventoryQuarantine(
        tenant_id=user.tenant_id,
        branch_id=inventory.branch_id,
        inventory_id=inventory.id,
        product_variant_id=inventory.product_variant_id,
        exchange_item_id=exchange_item.id,
        quantity=exchange_item.returned_quantity,
        status="PENDING",
        inspection_reason=reason_str[:255],
    )
    db.add(quarantine)
    db.flush()
    return quarantine


def exchange_sale_item(
    db: Session,
    sale_id: int,
    data: ItemExchangeRequest,
    current_user: User,
) -> dict[str, Any]:
    payload = data.model_dump(mode="json")
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    existing = db.scalar(select(GarmentExchange).where(GarmentExchange.tenant_id == current_user.tenant_id, GarmentExchange.idempotency_key == data.idempotency_key))
    if existing is not None:
        if existing.request_fingerprint != fingerprint:
            raise error("IDEMPOTENCY_KEY_CONFLICT", "La clave de idempotencia ya fue usada con otra solicitud.", status.HTTP_409_CONFLICT)
        return existing.result_json

    now = datetime.now(UTC)
    sale = db.scalar(select(Sale).where(Sale.id == sale_id).with_for_update())
    if sale is None:
        raise error("SALE_NOT_FOUND", "Venta no encontrada.", status.HTTP_404_NOT_FOUND)
    existing = db.scalar(select(GarmentExchange).where(GarmentExchange.tenant_id == current_user.tenant_id, GarmentExchange.idempotency_key == data.idempotency_key))
    if existing is not None:
        if existing.request_fingerprint != fingerprint:
            raise error("IDEMPOTENCY_KEY_CONFLICT", "La clave de idempotencia ya fue usada con otra solicitud.", status.HTTP_409_CONFLICT)
        return existing.result_json
    if sale.tenant_id is not None and current_user.tenant_id != sale.tenant_id:
        raise error("SALE_FORBIDDEN", "La venta no pertenece al tenant actual.", status.HTTP_403_FORBIDDEN)
    branch = db.scalar(select(Branch).where(Branch.id == sale.branch_id, Branch.is_active.is_(True)))
    if branch is None or (sale.tenant_id is not None and branch.tenant_id != sale.tenant_id):
        raise error("BRANCH_NOT_FOUND_OR_INACTIVE", "La sucursal no existe, está inactiva o no pertenece a la venta.", status.HTTP_403_FORBIDDEN)
    if current_user.role.code != "ADMIN" and sale.branch_id not in {branch.id for branch in current_user.branches}:
        raise error("SALE_FORBIDDEN", "No tienes acceso a la sucursal de la venta.", status.HTTP_403_FORBIDDEN)
    if sale.status not in ("COMPLETED", "CONFIRMED", "PENDING_DELIVERY", "DELIVERED"):
        raise error("SALE_NOT_ELIGIBLE_FOR_EXCHANGE", "Solo se pueden cambiar prendas de ventas completadas o confirmadas.", status.HTTP_400_BAD_REQUEST)

    sale_created = sale.created_at.replace(tzinfo=UTC) if sale.created_at.tzinfo is None else sale.created_at
    days_elapsed = max(0, (now - sale_created).days)
    store_days = _get_store_exchange_policy_days(branch, sale.tenant_id)

    items = db.scalars(select(SaleItem).where(SaleItem.sale_id == sale.id).with_for_update()).all()
    matching_item = next((item for item in items if item.product_variant_id == data.returned_variant_id), None)
    source_variant = db.scalar(select(ProductVariant).options(joinedload(ProductVariant.product).joinedload(Product.category)).where(ProductVariant.id == data.returned_variant_id, ProductVariant.is_active.is_(True)))
    replacement_variant = db.scalar(select(ProductVariant).options(joinedload(ProductVariant.product)).where(ProductVariant.id == data.new_variant_id, ProductVariant.is_active.is_(True)))
    if source_variant is None or not source_variant.product.is_active or replacement_variant is None or not replacement_variant.product.is_active:
        raise error("VARIANT_NOT_FOUND_OR_INACTIVE", "La variante de origen o reemplazo no existe o está inactiva.", status.HTTP_400_BAD_REQUEST)
    if (sale.tenant_id is not None and (source_variant.tenant_id != sale.tenant_id or replacement_variant.tenant_id != sale.tenant_id or source_variant.product.tenant_id != sale.tenant_id or replacement_variant.product.tenant_id != sale.tenant_id)):
        raise error("VARIANT_NOT_FOUND_OR_INACTIVE", "Las variantes no pertenecen al tenant de la venta.", status.HTTP_403_FORBIDDEN)
    _validate_product_catalog_status(source_variant.product)
    _validate_product_catalog_status(replacement_variant.product)

    item_days, item_policy_note = _resolve_product_exchange_policy(source_variant.product, store_days)
    if item_days == 0:
        raise error("ITEM_NOT_EXCHANGEABLE", f"La prenda '{source_variant.product.name}' no está sujeta a cambios por norma sanitaria y de higiene.", status.HTTP_400_BAD_REQUEST)
    if days_elapsed > item_days:
        raise error("EXCHANGE_WINDOW_EXPIRED", f"El plazo de cambio para esta prenda ({item_days} días) ha expirado (han transcurrido {days_elapsed} días desde la compra).", status.HTTP_400_BAD_REQUEST)

    # Validar condición física de la prenda según políticas de devolución
    item_condition = (data.item_condition or "EXCELLENT").upper()
    if item_condition == "REJECTED":
        raise error("ITEM_CONDITION_REJECTED", "La prenda no cumple las condiciones de la política de devoluciones y ha sido rechazada para cambio.", status.HTTP_400_BAD_REQUEST)

    if matching_item is None or matching_item.quantity < data.returned_quantity:
        raise error("ITEM_NOT_IN_SALE", "La prenda devuelta no corresponde a los items o cantidades de la venta.", status.HTTP_400_BAD_REQUEST)

    consumed = db.scalar(select(func.coalesce(func.sum(GarmentExchangeItem.returned_quantity), 0)).join(GarmentExchange).where(GarmentExchange.sale_id == sale.id, GarmentExchangeItem.sale_item_id == matching_item.id)) or 0
    if consumed + data.returned_quantity > matching_item.quantity:
        raise error("ITEM_ALREADY_EXCHANGED", "La cantidad solicitada ya fue cambiada previamente.", status.HTTP_409_CONFLICT)

    returned_value = (matching_item.line_total / matching_item.quantity * data.returned_quantity).quantize(Decimal("0.01"))
    delivered_value = (replacement_variant.product.price * data.new_quantity).quantize(Decimal("0.01"))
    difference = delivered_value - returned_value
    cash_tendered = data.cash_tendered if difference > 0 else None
    settlement = _exchange_cash_settlement(difference, cash_tendered)
    cash_change = settlement["cash_change"]
    cash_refunded = settlement["cash_refunded"]
    has_cash_origin = _is_cash_origin(sale.payments)
    if difference != 0 and not has_cash_origin:
        raise error("NON_CASH_DIFFERENCE_UNSUPPORTED", "Las diferencias no monetarias solo están soportadas para ventas de origen efectivo.", status.HTTP_409_CONFLICT)
    if difference > 0 and (data.cash_tendered is None or data.cash_tendered < difference):
        raise error("INSUFFICIENT_CASH_TENDER", "El efectivo recibido no cubre la diferencia del cambio.", status.HTTP_400_BAD_REQUEST)
    if difference < 0 and not data.cashier_confirmed:
        raise error("CASH_REFUND_CONFIRMATION_REQUIRED", "La devolución en efectivo requiere confirmación explícita del cajero.", status.HTTP_400_BAD_REQUEST)

    inventory_rows = {}
    for variant_id in sorted({data.returned_variant_id, data.new_variant_id}):
        row = db.scalar(select(Inventory).where(Inventory.tenant_id == current_user.tenant_id, Inventory.branch_id == sale.branch_id, Inventory.product_variant_id == variant_id).with_for_update())
        if row is None:
            raise error("NEW_ITEM_INVENTORY_NOT_FOUND", "No existe inventario para una variante del cambio.", status.HTTP_409_CONFLICT)
        inventory_rows[variant_id] = row
    new_inv = inventory_rows[data.new_variant_id]
    available_stock = new_inv.stock_quantity - new_inv.reserved_quantity
    if available_stock < data.new_quantity:
        raise error("INSUFFICIENT_STOCK", "Stock insuficiente para la nueva prenda solicitada.", status.HTTP_409_CONFLICT)
    quote_expires_at = data.quote_expires_at
    if quote_expires_at.tzinfo is None:
        quote_expires_at = quote_expires_at.replace(tzinfo=UTC)
    if now >= quote_expires_at:
        raise error("EXCHANGE_QUOTE_EXPIRED", "La cotización del cambio expiró; solicite una nueva cotización.", status.HTTP_409_CONFLICT)
    quote_binding = _quote_binding(current_user=current_user, sale=sale, sale_item=matching_item, returned_quantity=data.returned_quantity, new_variant_id=data.new_variant_id, new_quantity=data.new_quantity, consumed=consumed, replacement_price=replacement_variant.product.price, available_stock=available_stock, reserved_stock=new_inv.reserved_quantity, cash_settlement_eligible=has_cash_origin or difference == 0, quote_expires_at=quote_expires_at)
    expected_fingerprint = _sign_quote(quote_binding)
    if not hmac.compare_digest(expected_fingerprint, data.quote_fingerprint):
        raise error("EXCHANGE_QUOTE_STALE", "La cotización cambió; solicite una nueva cotización.", status.HTTP_409_CONFLICT)

    returned_inv = inventory_rows[data.returned_variant_id]
    before_delivery = new_inv.stock_quantity
    new_inv.stock_quantity -= data.new_quantity
    db.add(InventoryMovement(tenant_id=current_user.tenant_id, inventory_id=new_inv.id, movement_type="SALE", quantity=data.new_quantity, stock_before=before_delivery, stock_after=new_inv.stock_quantity, reason=f"Entrega por cambio de prenda en venta {sale.order_number}", reference_type="garment_exchange", reference_id=sale.id, created_by=current_user.id))

    if settlement["create_payment"]:
        db.add(Payment(tenant_id=current_user.tenant_id, sale_id=sale.id, method="CASH", provider="EXCHANGE_REGISTER", transaction_reference=f"EXCHANGE-{data.idempotency_key}", status="APPROVED", amount=difference, received_amount=cash_tendered, change_amount=cash_change, metadata_json={"exchange_idempotency_key": data.idempotency_key, "direction": "COLLECTION"}, paid_at=now))

    inspection_summary = f"Estado: {item_condition} | Inspección: {', '.join(data.inspection_checklist) if data.inspection_checklist else 'Conforme'}"
    result = {
        "sale_id": sale.id,
        "order_number": sale.order_number,
        "returned_variant_id": data.returned_variant_id,
        "returned_quantity": data.returned_quantity,
        "new_variant_id": data.new_variant_id,
        "new_quantity": data.new_quantity,
        "status": "EXCHANGED",
        "returned_value": returned_value,
        "delivered_value": delivered_value,
        "difference": difference,
        "cash_tendered": cash_tendered,
        "cash_change": cash_change,
        "cash_refunded": cash_refunded,
        "item_condition": item_condition,
        "inspection_summary": inspection_summary,
        "exchanged_at": now.isoformat(),
    }
    exchange = GarmentExchange(tenant_id=current_user.tenant_id, sale_id=sale.id, branch_id=sale.branch_id, idempotency_key=data.idempotency_key, request_fingerprint=fingerprint, returned_value=returned_value, delivered_value=delivered_value, difference=difference, cash_tendered=cash_tendered, cash_change=cash_change, cash_refunded=cash_refunded, cashier_confirmed=data.cashier_confirmed, result_json={})
    db.add(exchange)
    replay = _flush_exchange_or_replay(db, exchange, fingerprint)
    if replay is not None:
        return replay
    exchange_item = GarmentExchangeItem(exchange_id=exchange.id, sale_item_id=matching_item.id, returned_quantity=data.returned_quantity, new_variant_id=data.new_variant_id, new_quantity=data.new_quantity)
    db.add(exchange_item)
    db.flush()
    quarantine = create_exchange_quarantine(db, exchange_item, returned_inv, current_user, condition=item_condition, checklist=data.inspection_checklist, notes=data.condition_notes or data.reason)
    result["quarantine_id"] = quarantine.id
    result["quarantine_status"] = quarantine.status
    exchange.result_json = {key: (str(value) if isinstance(value, Decimal) else value) for key, value in result.items()}
    record_audit(db, current_user, "EXCHANGE", "garment_exchange", exchange.id, f"Cambio de prenda en venta {sale.order_number}", new_values={"difference": difference, "cash_tendered": cash_tendered, "cash_change": cash_change, "cashier_confirmed": data.cashier_confirmed, "item_condition": item_condition, "returned_inventory_status": "PENDING_QUARANTINE"})
    db.flush()
    return result
