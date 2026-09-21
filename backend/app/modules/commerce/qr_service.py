import urllib.parse
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.models import Payment, Sale, User
from app.modules.commerce import service
from app.modules.commerce.schemas import QRPaymentResponse, QRPaymentStatusResponse


def generate_qr_payment(
    db: Session,
    sale_id: int,
    current_user: User,
    client_base_url: str | None = None,
) -> QRPaymentResponse:
    sale = service.get_sale(db, sale_id)
    if sale.channel != "DIGITAL" or sale.status != "PENDING":
        raise service.error("INVALID_ELECTRONIC_SALE", "La venta digital no está pendiente de pago.", status.HTTP_409_CONFLICT)

    if current_user.role.code == "CLIENT" and sale.customer_id != current_user.id:
        raise service.error("SALE_FORBIDDEN", "No puedes consultar una venta de otro usuario.", status.HTTP_403_FORBIDDEN)

    # Base URL para escaneo móvil (si no se especifica, usa IP de red local o localhost)
    base_url = (client_base_url or "http://192.168.0.7:4200").rstrip("/")

    # Reutilizar pago QR pendiente existente si existe
    existing = db.scalar(
        select(Payment).where(
            Payment.sale_id == sale.id,
            Payment.provider == "QR_SIMPLE",
            Payment.status == "PENDING",
        )
    )
    if existing is not None:
        meta = existing.metadata_json or {}
        expires_at_str = meta.get("expires_at")
        expires_at = datetime.fromisoformat(expires_at_str) if expires_at_str else (datetime.now(UTC) + timedelta(minutes=15))
        return QRPaymentResponse(
            payment_id=existing.id,
            sale_id=existing.sale_id,
            order_number=sale.order_number,
            amount=existing.amount,
            currency="BOB",
            qr_data=meta.get("qr_data", ""),
            qr_image_url=meta.get("qr_image_url", ""),
            business_name=meta.get("business_name", "FashionStore Atelier S.R.L."),
            nit=meta.get("nit", "102938475"),
            bank_name=meta.get("bank_name", "Banco Nacional de Bolivia (BNB)"),
            transaction_reference=existing.transaction_reference or "",
            expires_at=expires_at,
            status=existing.status,
        )

    ref = f"QR-FASHION-{sale.order_number}-{uuid4().hex[:6].upper()}"
    expires_at = datetime.now(UTC) + timedelta(minutes=15)
    
    # Enlace de banca móvil que se abre al escanear con la cámara del celular
    mobile_banking_url = f"{base_url}/banca-movil?ref={ref}&amount={sale.total}&order={sale.order_number}"
    qr_image_url = f"https://api.qrserver.com/v1/create-qr-code/?size=280x280&margin=8&data={urllib.parse.quote(mobile_banking_url)}"

    payment = Payment(
        sale_id=sale.id,
        method="QR",
        provider="QR_SIMPLE",
        transaction_reference=ref,
        status="PENDING",
        amount=sale.total,
        idempotency_key=ref,
        metadata_json={
            "business_name": "FashionStore Atelier S.R.L.",
            "nit": "102938475",
            "bank_name": "Banco Nacional de Bolivia (BNB)",
            "account_number": "100-294857-19",
            "qr_data": mobile_banking_url,
            "qr_image_url": qr_image_url,
            "mobile_banking_url": mobile_banking_url,
            "expires_at": expires_at.isoformat(),
        },
    )
    db.add(payment)
    db.flush()

    return QRPaymentResponse(
        payment_id=payment.id,
        sale_id=payment.sale_id,
        order_number=sale.order_number,
        amount=payment.amount,
        currency="BOB",
        qr_data=mobile_banking_url,
        qr_image_url=qr_image_url,
        business_name="FashionStore Atelier S.R.L.",
        nit="102938475",
        bank_name="Banco Nacional de Bolivia (BNB)",
        transaction_reference=ref,
        expires_at=expires_at,
        status="PENDING",
    )


def check_qr_payment_status(db: Session, transaction_reference: str) -> QRPaymentStatusResponse:
    payment = db.scalar(
        select(Payment).where(
            Payment.transaction_reference == transaction_reference,
            Payment.provider == "QR_SIMPLE",
        )
    )
    if payment is None:
        raise service.error("PAYMENT_NOT_FOUND", "Transacción QR no encontrada.", status.HTTP_404_NOT_FOUND)

    sale = service.get_sale(db, payment.sale_id)
    return QRPaymentStatusResponse(
        transaction_reference=payment.transaction_reference,
        sale_id=sale.id,
        order_number=sale.order_number,
        amount=payment.amount,
        currency="BOB",
        status=payment.status,
        is_confirmed=payment.status == "APPROVED",
    )


def confirm_qr_transfer(
    db: Session,
    transaction_reference: str,
    amount: Decimal,
    current_user: User | None = None,
) -> Sale:
    payment = db.scalar(
        select(Payment).where(
            Payment.transaction_reference == transaction_reference,
            Payment.provider == "QR_SIMPLE",
        )
    )
    if payment is None:
        raise service.error("PAYMENT_NOT_FOUND", "Transacción QR no encontrada.", status.HTTP_404_NOT_FOUND)

    sale = service.get_sale(db, payment.sale_id)
    if current_user is not None and current_user.role.code == "CLIENT" and sale.customer_id != current_user.id:
        raise service.error("SALE_FORBIDDEN", "No puedes confirmar esta compra.", status.HTTP_403_FORBIDDEN)

    if payment.amount != amount:
        raise service.error(
            "PAYMENT_AMOUNT_MISMATCH",
            f"El monto transferido ({amount}) no coincide con el total de la venta ({payment.amount}).",
            status.HTTP_409_CONFLICT,
        )

    if payment.status == "APPROVED":
        return sale

    if payment.status in {"REJECTED", "CANCELLED"}:
        raise service.error("PAYMENT_TERMINAL_STATE", "El pago QR ya se encuentra en un estado terminal.", status.HTTP_409_CONFLICT)

    payment.status = "APPROVED"
    payment.received_amount = amount
    payment.paid_at = datetime.now(UTC)

    # Actor que autoriza la venta (el cliente propietario de la orden)
    payer = current_user
    if payer is None and sale.customer_id is not None:
        payer = db.get(User, sale.customer_id)
    if payer is None:
        payer = db.scalar(select(User).join(User.role).where(Role.code == "ADMIN"))

    service.confirm_sale(db, sale, payer)

    if sale.customer_id is not None:
        cart = service.get_cart(db, sale.customer_id)
        cart.items.clear()
        db.flush()

    db.flush()
    return sale


def simulate_or_confirm_qr_payment(
    db: Session,
    transaction_reference: str,
    amount: Decimal,
    current_user: User,
) -> Sale:
    return confirm_qr_transfer(db, transaction_reference, amount, current_user)
