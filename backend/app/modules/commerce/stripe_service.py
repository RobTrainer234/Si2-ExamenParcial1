import hmac
import hashlib
import time
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import httpx
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.models import Payment, Sale, User
from app.modules.commerce import service
from app.modules.commerce.schemas import StripePaymentIntentRequest, StripePaymentIntentResponse


def create_payment_intent(
    db: Session,
    data: StripePaymentIntentRequest,
    current_user: User,
) -> StripePaymentIntentResponse:
    sale = service.get_sale(db, data.sale_id)
    if sale.channel != "DIGITAL" or sale.status != "PENDING":
        raise service.error("INVALID_ELECTRONIC_SALE", "La venta digital no está pendiente de pago.", status.HTTP_409_CONFLICT)

    if current_user.role.code == "CLIENT" and sale.customer_id != current_user.id:
        raise service.error("SALE_FORBIDDEN", "No puedes pagar una venta de otro usuario.", status.HTTP_403_FORBIDDEN)

    # Idempotencia
    existing = db.scalar(select(Payment).where(Payment.idempotency_key == data.idempotency_key))
    if existing is not None:
        if existing.sale_id != data.sale_id:
            raise service.error("IDEMPOTENCY_KEY_CONFLICT", "La clave de idempotencia ya fue usada para otra venta.", status.HTTP_409_CONFLICT)
        metadata = existing.metadata_json or {}
        return StripePaymentIntentResponse(
            payment_id=existing.id,
            sale_id=existing.sale_id,
            provider="STRIPE",
            payment_intent_id=existing.transaction_reference or "",
            client_secret=metadata.get("client_secret", ""),
            amount=existing.amount,
            currency=metadata.get("currency", (settings.stripe_currency or "bob")).upper(),
            status=existing.status,
        )

    amount_cents = int(round(float(sale.total) * 100))
    currency = (settings.stripe_currency or "bob").lower()

    intent_id: str
    client_secret: str

    if settings.stripe_secret_key and not settings.stripe_secret_key.startswith("sk_test_mock"):
        try:
            resp = httpx.post(
                "https://api.stripe.com/v1/payment_intents",
                headers={
                    "Authorization": f"Bearer {settings.stripe_secret_key}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "amount": str(amount_cents),
                    "currency": currency,
                    "payment_method_types[]": "card",
                    "description": f"FashionStore Pedido {sale.order_number}",
                    "metadata[sale_id]": str(sale.id),
                    "metadata[order_number]": sale.order_number,
                    "metadata[customer_id]": str(current_user.id),
                },
                timeout=20.0,
            )
            if resp.status_code != 200:
                err_body = resp.json()
                err_msg = err_body.get("error", {}).get("message", "Error devuelto por la pasarela Stripe.")
                raise service.error("STRIPE_API_ERROR", err_msg, status.HTTP_400_BAD_REQUEST)

            payload = resp.json()
            intent_id = payload["id"]
            client_secret = payload.get("client_secret", "")
        except httpx.RequestError as exc:
            raise service.error("STRIPE_COMMUNICATION_ERROR", f"No se pudo contactar con Stripe: {exc}", status.HTTP_502_BAD_GATEWAY)
    else:
        # Modo simulado para pruebas locales o cuando no hay clave real
        intent_id = f"pi_mock_{sale.id}_{uuid4().hex[:12]}"
        client_secret = f"{intent_id}_secret_{uuid4().hex[:16]}"

    payment = Payment(
        sale_id=sale.id,
        method="CARD",
        provider="STRIPE",
        transaction_reference=intent_id,
        status="PENDING",
        amount=sale.total,
        idempotency_key=data.idempotency_key,
        metadata_json={
            "client_secret": client_secret,
            "currency": currency.upper(),
            "order_number": sale.order_number,
        },
    )
    db.add(payment)
    db.flush()

    return StripePaymentIntentResponse(
        payment_id=payment.id,
        sale_id=sale.id,
        provider="STRIPE",
        payment_intent_id=intent_id,
        client_secret=client_secret,
        amount=sale.total,
        currency=currency.upper(),
        status="PENDING",
    )


def confirm_stripe_payment(db: Session, payment_intent_id: str, current_user: User) -> Sale:
    payment = db.scalar(
        select(Payment).where(
            Payment.transaction_reference == payment_intent_id,
            Payment.provider == "STRIPE",
        )
    )
    if payment is None:
        raise service.error("PAYMENT_NOT_FOUND", "Intención de pago de Stripe no encontrada.", status.HTTP_404_NOT_FOUND)

    sale = service.get_sale(db, payment.sale_id)
    if current_user.role.code == "CLIENT" and sale.customer_id != current_user.id:
        raise service.error("SALE_FORBIDDEN", "No puedes confirmar esta compra.", status.HTTP_403_FORBIDDEN)

    if payment.status == "APPROVED":
        return sale

    if payment.status in {"REJECTED", "CANCELLED"}:
        raise service.error("PAYMENT_TERMINAL_STATE", "El pago ya se encuentra en un estado terminal.", status.HTTP_409_CONFLICT)

    # Si hay clave real y no es un mock, verificar estado en Stripe
    if settings.stripe_secret_key and not settings.stripe_secret_key.startswith("sk_test_mock") and not payment_intent_id.startswith("pi_mock_"):
        try:
            resp = httpx.get(
                f"https://api.stripe.com/v1/payment_intents/{payment_intent_id}",
                headers={"Authorization": f"Bearer {settings.stripe_secret_key}"},
                timeout=15.0,
            )
            if resp.status_code == 200:
                intent_data = resp.json()
                stripe_status = intent_data.get("status")
                if stripe_status not in ("succeeded", "processing", "requires_capture"):
                    raise service.error(
                        "STRIPE_PAYMENT_NOT_SUCCEEDED",
                        f"El pago aún no ha sido completado en Stripe. Estado actual: {stripe_status}",
                        status.HTTP_400_BAD_REQUEST,
                    )
            elif resp.status_code != 200:
                err_msg = resp.json().get("error", {}).get("message", "Error al verificar con Stripe.")
                raise service.error("STRIPE_VERIFY_ERROR", err_msg, status.HTTP_400_BAD_REQUEST)
        except httpx.RequestError as exc:
            raise service.error("STRIPE_COMMUNICATION_ERROR", f"Error de comunicación con Stripe: {exc}", status.HTTP_502_BAD_GATEWAY)

    # Confirmar pago y venta
    payment.status = "APPROVED"
    payment.paid_at = datetime.now(UTC)
    service.confirm_sale(db, sale, current_user)

    if sale.customer_id is not None:
        cart = service.get_cart(db, sale.customer_id)
        cart.items.clear()
        db.flush()

    db.flush()
    return sale


def verify_stripe_webhook_signature(payload: bytes, sig_header: str, secret: str) -> bool:
    """Verificación de firma v1 de webhook de Stripe (HMAC-SHA256)."""
    try:
        parts = dict(pair.split("=", 1) for pair in sig_header.split(","))
        timestamp = parts.get("t")
        expected_sig = parts.get("v1")
        if not timestamp or not expected_sig:
            return False

        # Rechazar mensajes más antiguos de 5 minutos
        if abs(time.time() - int(timestamp)) > 300:
            return False

        signed_payload = f"{timestamp}.".encode("utf-8") + payload
        computed_sig = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed_sig, expected_sig)
    except Exception:
        return False


def handle_stripe_webhook(db: Session, payload: bytes, sig_header: str | None) -> dict:
    if settings.stripe_webhook_secret:
        if not sig_header or not verify_stripe_webhook_signature(payload, sig_header, settings.stripe_webhook_secret):
            raise service.error("INVALID_WEBHOOK_SIGNATURE", "Firma de webhook de Stripe no válida.", status.HTTP_401_UNAUTHORIZED)

    import json
    try:
        event = json.loads(payload.decode("utf-8"))
    except Exception:
        raise service.error("INVALID_WEBHOOK_PAYLOAD", "Cuerpo del webhook no es JSON válido.", status.HTTP_400_BAD_REQUEST)

    event_type = event.get("type")
    data_object = event.get("data", {}).get("object", {})

    if event_type == "payment_intent.succeeded":
        intent_id = data_object.get("id")
        if intent_id:
            payment = db.scalar(select(Payment).where(Payment.transaction_reference == intent_id, Payment.provider == "STRIPE"))
            if payment and payment.status != "APPROVED":
                payment.status = "APPROVED"
                payment.paid_at = datetime.now(UTC)
                sale = service.get_sale(db, payment.sale_id)
                service.confirm_sale(db, sale, None)
                if sale.customer_id is not None:
                    cart = service.get_cart(db, sale.customer_id)
                    cart.items.clear()
                    db.flush()
                db.commit()

    elif event_type == "payment_intent.payment_failed":
        intent_id = data_object.get("id")
        if intent_id:
            payment = db.scalar(select(Payment).where(Payment.transaction_reference == intent_id, Payment.provider == "STRIPE"))
            if payment and payment.status == "PENDING":
                payment.status = "FAILED"
                sale = service.get_sale(db, payment.sale_id)
                sale.status = "FAILED"
                db.commit()

    return {"received": True, "event": event_type}
