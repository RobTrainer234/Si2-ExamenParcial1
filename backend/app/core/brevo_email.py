from __future__ import annotations

import httpx
from fastapi import HTTPException, status

from app.core.config import settings

BREVO_TRANSACTIONAL_URL = "https://api.brevo.com/v3/smtp/email"


def generate_verification_code() -> str:
    import secrets
    return f"{secrets.randbelow(1_000_000):06d}"


def send_transactional_email(*, recipient_email: str, subject: str, html_content: str, text_content: str | None = None) -> None:
    if not settings.brevo_api_key or not settings.brevo_sender_email:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"code": "EMAIL_NOT_CONFIGURED", "message": "El servicio de correo no está disponible."})
    payload = {
        "sender": {"email": settings.brevo_sender_email, **({"name": settings.brevo_sender_name} if settings.brevo_sender_name else {})},
        "to": [{"email": recipient_email}],
        "subject": subject,
        "htmlContent": html_content,
    }
    if text_content:
        payload["textContent"] = text_content
    try:
        response = httpx.post(BREVO_TRANSACTIONAL_URL, headers={"api-key": settings.brevo_api_key, "accept": "application/json", "content-type": "application/json"}, json=payload, timeout=15.0)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail={"code": "EMAIL_PROVIDER_UNAVAILABLE", "message": "No se pudo enviar el correo."}) from exc
    if response.status_code not in (200, 201, 202):
        raise HTTPException(status_code=502, detail={"code": "EMAIL_PROVIDER_ERROR", "message": "No se pudo enviar el correo."})
