from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import settings


def verify_webhook_signature(payload: bytes, signature: str | None, secret: str | None) -> bool:
    """Verify Stripe's timestamped v1 signature; absent secrets always reject."""
    if not secret or not signature:
        return False
    try:
        parts = dict(item.split("=", 1) for item in signature.split(",") if "=" in item)
        timestamp = parts.get("t")
        provided = parts.get("v1")
        if not timestamp or not provided or abs(time.time() - int(timestamp)) > 300:
            return False
        signed = f"{timestamp}.".encode() + payload
        expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, provided)
    except (TypeError, ValueError):
        return False


def handle_webhook(db: Any, payload: bytes, signature: str | None) -> dict[str, Any]:
    if not settings.stripe_webhook_secret or not verify_webhook_signature(payload, signature, settings.stripe_webhook_secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "INVALID_WEBHOOK_SIGNATURE", "message": "Firma de webhook de Stripe no válida."})
    try:
        event = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "INVALID_WEBHOOK_PAYLOAD", "message": "Cuerpo del webhook no es JSON válido."})
    if not isinstance(event, dict) or not event.get("id") or not event.get("type"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "INVALID_WEBHOOK_EVENT", "message": "Webhook event id and type are required."})
    from app.modules.subscriptions import service
    return service.handle_stripe_webhook(db, event)


def create_checkout_session(**kwargs: Any) -> dict[str, Any]:
    """Create a hosted recurring Checkout Session at Stripe's HTTP boundary."""
    if not settings.stripe_secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "STRIPE_NOT_CONFIGURED", "message": "Stripe no está configurado."},
        )

    form: dict[str, str] = {
        "mode": kwargs["mode"],
        "success_url": kwargs["success_url"],
        "cancel_url": kwargs["cancel_url"],
        "line_items[0][price_data][currency]": kwargs["line_items"][0]["price_data"]["currency"],
        "line_items[0][price_data][unit_amount]": str(kwargs["line_items"][0]["price_data"]["unit_amount"]),
        "line_items[0][price_data][recurring][interval]": kwargs["line_items"][0]["price_data"]["recurring"]["interval"],
        "line_items[0][price_data][product_data][name]": kwargs["line_items"][0]["price_data"]["product_data"]["name"],
        "line_items[0][quantity]": "1",
    }
    if kwargs.get("customer_email"):
        form["customer_email"] = str(kwargs["customer_email"])
    for key, value in kwargs.get("metadata", {}).items():
        form[f"metadata[{key}]"] = str(value)

    try:
        headers = {"Authorization": f"Bearer {settings.stripe_secret_key}"}
        if kwargs.get("idempotency_key"):
            headers["Idempotency-Key"] = kwargs["idempotency_key"]
        response = httpx.post(
            "https://api.stripe.com/v1/checkout/sessions",
            headers=headers,
            data=form,
            timeout=15.0,
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "STRIPE_COMMUNICATION_ERROR", "message": "No se pudo contactar con Stripe."},
        ) from exc

    if response.status_code not in (200, 201):
        message = response.json().get("error", {}).get("message", "Stripe rechazó la sesión de checkout.")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail={"code": "STRIPE_API_ERROR", "message": message})
    payload = response.json()
    if not payload.get("id") or not payload.get("url"):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail={"code": "STRIPE_INVALID_RESPONSE", "message": "Stripe devolvió una sesión incompleta."})
    return payload
