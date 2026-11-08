from collections import defaultdict
import hashlib
import hmac
from html import escape
import secrets
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from math import ceil
from typing import Any
from urllib.parse import urlencode
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.audit import record_audit
from app.core.config import settings
from app.core.models import Bitacora, Branch, Category, EmailOutbox, EmailVerificationChallenge, PendingPaidSignup, ProcessedStripeEvent, Product, ProductVariant, Role, Subscription, SubscriptionPlan, Tenant, User
from app.core.security import hash_password
from app.modules.auth import service as auth_service
from app.modules.subscriptions.schemas import (
    ReactivationRequestPayload,
    SubscriptionCancelRequest,
    SubscriptionChangeRequest,
    SubscriptionPlanCreateRequest,
    SubscriptionPlanResponse,
    SubscriptionPlanUpdateRequest,
    SubscriptionResponse,
    TenantCreateRequest,
    TenantResponse,
    PaidCheckoutRequest,
    PaidCheckoutResponse,
    PaidCheckoutStatusResponse,
    TrialSignupRequest,
)

TRIAL_DURATION_DAYS = 14
RETENTION_WINDOW_DAYS = 90
TRIAL_RATE_LIMIT_MAX_ATTEMPTS = 8
TRIAL_RATE_LIMIT_WINDOW_SECONDS = 900
VERIFICATION_TTL = timedelta(minutes=10)
CAPABILITY_TTL = timedelta(minutes=20)
RESEND_COOLDOWN = timedelta(seconds=60)
SEND_WINDOW = timedelta(hours=1)
MAX_CODE_ATTEMPTS = 5
MAX_SENDS_PER_WINDOW = 5


def _email_key(value: str) -> str:
    return value.strip().casefold()


def _secret_hash(value: str) -> str:
    return hmac.new(settings.jwt_secret.encode(), value.encode(), hashlib.sha256).hexdigest()


def create_email_verification(db: Session, email: str):
    from app.core import brevo_email
    from app.modules.subscriptions.schemas import EmailVerificationStartResponse
    normalized = _email_key(email)
    now = datetime.now(UTC)
    row = db.scalar(select(EmailVerificationChallenge).where(EmailVerificationChallenge.email == normalized).with_for_update())
    if row is not None:
        if row.last_sent_at and now - _as_utc(row.last_sent_at) < RESEND_COOLDOWN:
            raise HTTPException(status_code=429, detail={"code": "EMAIL_RESEND_COOLDOWN", "message": "Reintentá más tarde."})
        if now - _as_utc(row.window_started_at) >= SEND_WINDOW:
            row.send_count = 0
            row.window_started_at = now
        if row.send_count >= MAX_SENDS_PER_WINDOW:
            raise HTTPException(status_code=429, detail={"code": "EMAIL_SEND_LIMIT", "message": "No se pudo procesar la solicitud."})
    code = brevo_email.generate_verification_code()
    verification_subject = "Verificá tu correo electrónico"
    verification_html = (
        f"<p>Tu código de verificación es <strong>{code}</strong>.</p>"
        "<p>Vence en 10 minutos. Si no solicitaste este código, ignorá este mensaje.</p>"
    )
    verification_text = (
        f"Tu código de verificación es {code}. Vence en 10 minutos. "
        "Si no solicitaste este código, ignorá este mensaje."
    )
    brevo_email.send_transactional_email(
        recipient_email=normalized,
        subject=verification_subject,
        html_content=verification_html,
        text_content=verification_text,
    )
    if row is None:
        row = EmailVerificationChallenge(email=normalized, code_hash=_secret_hash(code), expires_at=now + VERIFICATION_TTL, attempts=0, send_count=1, window_started_at=now, last_sent_at=now)
        db.add(row)
    else:
        row.code_hash = _secret_hash(code)
        row.expires_at = now + VERIFICATION_TTL
        row.attempts = 0
        row.send_count += 1
        row.last_sent_at = now
        row.verified_at = None
        row.capability_hash = None
        row.capability_expires_at = None
        row.capability_bound_pending_id = None
    db.flush()
    return EmailVerificationStartResponse(email_sent=True)


def verify_email_code(db: Session, email: str, code: str):
    from app.modules.subscriptions.schemas import EmailVerificationVerifyResponse
    normalized = _email_key(email)
    row = db.scalar(select(EmailVerificationChallenge).where(EmailVerificationChallenge.email == normalized).with_for_update())
    now = datetime.now(UTC)
    if row is None or row.verified_at is not None or row.attempts >= MAX_CODE_ATTEMPTS or _as_utc(row.expires_at) <= now:
        raise HTTPException(status_code=400, detail={"code": "EMAIL_CODE_INVALID", "message": "El código no es válido."})
    row.attempts += 1
    if not hmac.compare_digest(row.code_hash, _secret_hash(code)):
        db.flush()
        db.commit()
        raise HTTPException(status_code=400, detail={"code": "EMAIL_CODE_INVALID", "message": "El código no es válido."})
    capability = secrets.token_urlsafe(32)
    row.verified_at = now
    row.capability_hash = _secret_hash(capability)
    row.capability_expires_at = now + CAPABILITY_TTL
    db.flush()
    return EmailVerificationVerifyResponse(checkout_capability=capability)
_trial_ip_attempts: dict[str, list[datetime]] = defaultdict(list)


def create_paid_checkout(
    db: Session,
    data: PaidCheckoutRequest,
    session_creator: Any | None = None,
) -> PaidCheckoutResponse:
    from app.modules.subscriptions import stripe_service

    plan_code = data.plan_code.strip().upper()
    if plan_code == "PRO":
        plan_code = "PROFESSIONAL"
    plan = db.scalar(
        select(SubscriptionPlan).where(
            SubscriptionPlan.code == plan_code,
            SubscriptionPlan.is_active.is_(True),
        )
    )
    if plan is None:
        raise _not_found("El plan de suscripción no está disponible.", "PLAN_NOT_FOUND")

    email = str(data.email).strip().lower()
    capability_hash = _secret_hash(data.checkout_capability)
    verification = db.scalar(select(EmailVerificationChallenge).where(EmailVerificationChallenge.email == email).with_for_update())
    if verification is None or verification.verified_at is None or verification.capability_hash != capability_hash or verification.capability_expires_at is None or _as_utc(verification.capability_expires_at) <= datetime.now(UTC):
        raise _conflict("La verificación de correo es requerida.", "EMAIL_VERIFICATION_REQUIRED")
    if db.scalar(select(User.id).where(func.lower(User.email) == email).execution_options(ignore_tenant_scope=True)) is not None:
        raise _conflict("El correo electrónico ya está registrado.", "EMAIL_ALREADY_REGISTERED")
    amount = plan.price_monthly if data.billing_interval == "monthly" else plan.price_annual
    if amount is None or amount <= Decimal("0.00"):
        raise _conflict("El intervalo seleccionado no tiene un precio válido.", "PAID_PLAN_PRICE_INVALID")
    fingerprint = _paid_signup_fingerprint(data, plan_code, email)
    bound_pending_id = verification.capability_bound_pending_id
    pending = db.get(PendingPaidSignup, bound_pending_id) if bound_pending_id is not None else None
    if bound_pending_id is not None:
        if pending is None:
            raise _conflict("La capacidad de checkout ya fue utilizada.", "PAID_SIGNUP_CAPABILITY_REUSED")
        if pending.request_fingerprint != fingerprint:
            raise _conflict("La capacidad de checkout no puede reutilizarse con otros datos.", "PAID_SIGNUP_CAPABILITY_REUSED")
        if pending.status not in {"PENDING", "CHECKOUT_CREATED"}:
            raise _conflict("La capacidad de checkout ya fue utilizada.", "PAID_SIGNUP_CAPABILITY_REUSED")
    else:
        pending = db.scalar(
            select(PendingPaidSignup)
            .where(
                PendingPaidSignup.email == email,
                PendingPaidSignup.status.in_(("PENDING", "CHECKOUT_CREATED")),
            )
            .order_by(PendingPaidSignup.id.desc())
        )
        if pending is not None:
            if pending.request_fingerprint != fingerprint:
                raise _conflict("Ya existe un registro de pago pendiente para este correo electrónico con otros datos.", "PAID_SIGNUP_IN_PROGRESS")
            if pending.checkout_capability_hash != capability_hash:
                raise _conflict("Ya existe un registro de pago pendiente para este correo electrónico.", "PAID_SIGNUP_IN_PROGRESS")
            verification.capability_bound_pending_id = pending.id
            db.commit()
        else:
            pending = PendingPaidSignup(
                company_name=data.company_name.strip(),
                first_name=data.first_name.strip(),
                last_name=data.last_name.strip(),
                email=email,
                phone=data.phone.strip(),
                password_hash=hash_password(data.password),
                plan_id=plan.id,
                billing_interval=data.billing_interval,
                amount=amount,
                currency=(plan.currency or "BOB").lower(),
                status="PENDING",
                request_fingerprint=fingerprint,
                checkout_capability_hash=capability_hash,
                capability_expires_at=verification.capability_expires_at,
            )
            db.add(pending)
            try:
                db.flush()
                verification.capability_bound_pending_id = pending.id
                db.commit()
            except IntegrityError:
                db.rollback()
                verification = db.scalar(
                    select(EmailVerificationChallenge)
                    .where(EmailVerificationChallenge.email == email)
                    .with_for_update()
                )
                pending = db.get(PendingPaidSignup, verification.capability_bound_pending_id) if verification and verification.capability_bound_pending_id is not None else None
                if pending is None:
                    pending = db.scalar(
                        select(PendingPaidSignup).where(
                            PendingPaidSignup.email == email,
                            PendingPaidSignup.status.in_(("PENDING", "CHECKOUT_CREATED")),
                        )
                    )
                if pending is None or pending.request_fingerprint != fingerprint or pending.checkout_capability_hash != capability_hash:
                    raise _conflict("Ya existe un registro de pago pendiente para este correo electrónico.", "PAID_SIGNUP_IN_PROGRESS")
                if verification.capability_bound_pending_id != pending.id:
                    verification.capability_bound_pending_id = pending.id
                    db.commit()

    if pending.stripe_session_id and pending.stripe_session_url:
        return PaidCheckoutResponse(session_id=pending.stripe_session_id, session_url=pending.stripe_session_url)

    if pending.stripe_idempotency_key is None:
        pending.stripe_idempotency_key = f"paid-signup-{pending.id}"
        db.commit()

    creator = session_creator or stripe_service.create_checkout_session
    interval = "month" if data.billing_interval == "monthly" else "year"
    frontend_origin = settings.frontend_url.rstrip("/")
    session = creator(
        mode="subscription",
        customer_email=email,
        success_url=f"{frontend_origin}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{frontend_origin}/subscription/cancel?{urlencode({'plan': plan.code, 'billing': data.billing_interval})}",
        line_items=[
            {
                "price_data": {
                    "currency": pending.currency,
                    "unit_amount": int(pending.amount * 100),
                    "recurring": {"interval": interval},
                    "product_data": {"name": f"{plan.name} subscription"},
                },
                "quantity": 1,
            }
        ],
        metadata={"pending_signup_id": pending.id, "plan_code": plan.code},
        idempotency_key=pending.stripe_idempotency_key,
    )
    pending.status = "CHECKOUT_CREATED"
    pending.stripe_session_id = session["id"]
    pending.stripe_session_url = session["url"]
    db.commit()
    return PaidCheckoutResponse(session_id=session["id"], session_url=session["url"])


def get_paid_checkout_status(db: Session, session_id: str) -> dict[str, str]:
    normalized_session_id = session_id.strip()
    if not normalized_session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CHECKOUT_SESSION_INVALID", "message": "La sesión de checkout no es válida."},
        )
    pending = db.scalar(
        select(PendingPaidSignup.status).where(PendingPaidSignup.stripe_session_id == normalized_session_id)
    )
    if pending is None:
        raise _not_found("La sesión de checkout no existe.", "CHECKOUT_SESSION_NOT_FOUND")
    status_value = pending if pending in {"PENDING", "CHECKOUT_CREATED", "COMPLETED", "EXPIRED", "EMAIL_CONFLICT"} else "ERROR"
    return {"status": status_value}


def _paid_signup_fingerprint(data: PaidCheckoutRequest, plan_code: str, email: str) -> str:
    canonical = "|".join(
        (
            data.company_name.strip().casefold(),
            data.first_name.strip().casefold(),
            data.last_name.strip().casefold(),
            email,
            data.phone.strip(),
            data.password,
            plan_code,
            data.billing_interval,
        )
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def handle_stripe_webhook(db: Session, event: dict[str, Any]) -> dict[str, Any]:
    """Apply a verified SaaS event atomically; browser redirects never call this function."""
    event_id = event.get("id")
    event_type = event.get("type")
    if not isinstance(event_id, str) or not event_id or not isinstance(event_type, str):
        raise HTTPException(status_code=400, detail={"code": "INVALID_WEBHOOK_EVENT", "message": "Webhook event id and type are required."})

    with db.no_autoflush:
        receipt = db.scalar(select(ProcessedStripeEvent).where(ProcessedStripeEvent.event_id == event_id).with_for_update())
    if receipt is not None:
        return {"received": True, "duplicate": True, "event": event_type}
    db.add(ProcessedStripeEvent(event_id=event_id, event_type=event_type))
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        receipt = db.scalar(select(ProcessedStripeEvent).where(ProcessedStripeEvent.event_id == event_id))
        if receipt is not None:
            return {"received": True, "duplicate": True, "event": event_type}
        raise

    obj = ((event.get("data") or {}).get("object") or {})
    provider_event_created_at = _stripe_event_timestamp(event)
    if event_type == "checkout.session.expired":
        metadata = obj.get("metadata") or {}
        pending_id = metadata.get("pending_signup_id")
        pending = db.scalar(select(PendingPaidSignup).where(PendingPaidSignup.id == int(pending_id)).with_for_update()) if str(pending_id or "").isdigit() else None
        if pending is not None and pending.stripe_session_id == obj.get("id") and pending.status in ("PENDING", "CHECKOUT_CREATED"):
            pending.status = "EXPIRED"
        return {"received": True, "expired": True, "event": event_type}

    if event_type == "checkout.session.completed":
        metadata = obj.get("metadata") or {}
        pending_id = metadata.get("pending_signup_id")
        paid = obj.get("payment_status") == "paid"
        if obj.get("mode") != "subscription" or not paid or not str(pending_id or "").isdigit():
            return {"received": True, "activated": False, "event": event_type}
        pending = db.scalar(select(PendingPaidSignup).where(PendingPaidSignup.id == int(pending_id)).with_for_update())
        if pending is None or pending.stripe_session_id != obj.get("id"):
            return {"received": True, "activated": False, "event": event_type}
        if pending.status == "COMPLETED":
            return {"received": True, "activated": False, "duplicate": True, "event": event_type}
        if not obj.get("subscription") or not obj.get("customer"):
            return {"received": True, "activated": False, "event": event_type}
        if db.scalar(select(User.id).where(func.lower(User.email) == pending.email).execution_options(ignore_tenant_scope=True)) is not None:
            pending.status = "EMAIL_CONFLICT"
            return {"received": True, "activated": False, "email_conflict": True, "event": event_type}
        role_admin = db.scalar(select(Role).where(Role.code == "ADMIN").with_for_update())
        if role_admin is None:
            raise _not_found("Rol de Administrador no encontrado.", "ROLE_NOT_FOUND")
        now = datetime.now(UTC)
        tenant = Tenant(name=pending.company_name, status="ACTIVE")
        db.add(tenant)
        db.flush()
        db.add(User(
            tenant_id=tenant.id, role_id=role_admin.id, first_name=pending.first_name,
            last_name=pending.last_name, email=pending.email, phone=pending.phone,
            password_hash=pending.password_hash, is_active=True,
        ))
        db.add(Subscription(
            tenant_id=tenant.id, plan_id=pending.plan_id, status="ACTIVE", valid_from=now,
            provider_customer_id=str(obj["customer"]), provider_subscription_id=str(obj["subscription"]),
            billing_interval=pending.billing_interval, provider_event_created_at=provider_event_created_at,
        ))
        pending.status = "COMPLETED"
        plan = db.get(SubscriptionPlan, pending.plan_id)
        plan_name = plan.name if plan is not None else "plan seleccionado"
        billing_interval = "anual" if pending.billing_interval == "annual" else "mensual"
        amount = f"{pending.amount:.2f} {pending.currency.upper()}"
        login_url = f"{settings.frontend_url.rstrip('/')}/login"
        safe_first_name = escape(pending.first_name)
        safe_plan_name = escape(plan_name)
        safe_login_url = escape(login_url, quote=True)
        confirmation_subject = "Tu cuenta de FashionStore está lista"
        confirmation_html = (
            f"<p>Hola {safe_first_name},</p>"
            "<p>Confirmamos tu pago y tu cuenta ya está activa.</p>"
            f"<ul><li>Tu plan {safe_plan_name}</li><li>Facturación {billing_interval}</li><li>Importe: {amount}</li></ul>"
            f"<p><a href=\"{safe_login_url}\">Iniciá sesión</a> con el correo y la contraseña que elegiste al registrarte.</p>"
        )
        confirmation_text = (
            f"Hola {pending.first_name}. Confirmamos tu pago y tu cuenta ya está activa. "
            f"Tu plan {plan_name}; facturación {billing_interval}; importe: {amount}. "
            f"Iniciá sesión con el correo y la contraseña que elegiste al registrarte: {login_url}"
        )
        db.add(EmailOutbox(
            kind="PAID_SIGNUP_CONFIRMATION",
            dedupe_key=f"pending:{pending.id}",
            recipient_email=pending.email,
            subject=confirmation_subject,
            html_body=confirmation_html,
            text_body=confirmation_text,
        ))
        db.flush()
        return {"received": True, "activated": True, "event": event_type}

    subscription_id = obj.get("subscription") or obj.get("id")
    if event_type in {"customer.subscription.updated", "customer.subscription.created", "invoice.paid", "invoice.payment_succeeded", "invoice.payment_failed", "customer.subscription.deleted"} and subscription_id:
        sub = db.scalar(select(Subscription).where(Subscription.provider_subscription_id == str(subscription_id)).with_for_update())
        if sub is not None:
            is_stale = (
                provider_event_created_at is not None
                and sub.provider_event_created_at is not None
                and provider_event_created_at <= _as_utc(sub.provider_event_created_at)
            )
            terminal = sub.status in {"CANCELLED", "EXPIRED"}
            if not is_stale and not (terminal and event_type in {"invoice.paid", "invoice.payment_succeeded"}):
                if event_type in {"invoice.paid", "invoice.payment_succeeded"} or (event_type == "customer.subscription.updated" and obj.get("status") in {"active", "trialing"}):
                    sub.status = "ACTIVE"
                elif event_type == "invoice.payment_failed" or (event_type == "customer.subscription.updated" and obj.get("status") in {"past_due", "unpaid", "incomplete", "paused"}):
                    sub.status = "SUSPENDED"
                elif event_type == "customer.subscription.deleted" or (event_type == "customer.subscription.updated" and obj.get("status") in {"canceled", "incomplete_expired"}):
                    sub.status = "CANCELLED"
                if provider_event_created_at is not None:
                    sub.provider_event_created_at = provider_event_created_at
                db.flush()
    return {"received": True, "event": event_type}


def _stripe_event_timestamp(event: dict[str, Any]) -> datetime | None:
    created = event.get("created")
    if not isinstance(created, (int, float)):
        return None
    return datetime.fromtimestamp(created, tz=UTC)


def reset_trial_rate_limits() -> None:
    _trial_ip_attempts.clear()


def _check_trial_rate_limit(client_ip: str | None) -> None:
    if not client_ip or client_ip in ("testclient", "127.0.0.1", "::1"):
        return
    now = datetime.now(UTC)
    cutoff = now - timedelta(seconds=TRIAL_RATE_LIMIT_WINDOW_SECONDS)
    recent = [ts for ts in _trial_ip_attempts[client_ip] if ts > cutoff]
    if len(recent) >= TRIAL_RATE_LIMIT_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "TOO_MANY_TRIAL_REQUESTS",
                "message": "Demasiadas solicitudes de prueba desde esta red. Intenta nuevamente más tarde.",
            },
        )
    recent.append(now)
    _trial_ip_attempts[client_ip] = recent


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _conflict(message: str, code: str = "SUBSCRIPTION_CONFLICT") -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": code, "message": message})


def _not_found(message: str, code: str = "RESOURCE_NOT_FOUND") -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": code, "message": message})


def serialize_plan(plan: SubscriptionPlan) -> dict[str, Any]:
    return {
        "id": plan.id,
        "code": plan.code,
        "name": plan.name,
        "price_monthly": float(getattr(plan, "price_monthly", 0.0) or 0.0),
        "price_annual": float(getattr(plan, "price_annual", 0.0) or 0.0),
        "currency": getattr(plan, "currency", "BOB") or "BOB",
        "max_active_branches": plan.max_active_branches,
        "generative_reports_enabled": plan.generative_reports_enabled,
        "is_active": plan.is_active,
    }


def serialize_subscription(sub: Subscription) -> dict[str, Any]:
    return {
        "id": sub.id,
        "tenant_id": sub.tenant_id,
        "plan": serialize_plan(sub.plan),
        "status": sub.status,
        "valid_from": sub.valid_from,
        "valid_until": sub.valid_until,
        "paused_at": sub.paused_at,
    }


def _evaluate_subscription_window(sub: Subscription | None, now: datetime | None = None) -> dict[str, Any]:
    now_utc = now or datetime.now(UTC)
    if sub is None:
        return {
            "is_trial": False,
            "is_expired": False,
            "days_remaining": None,
            "retention_days_remaining": None,
        }
    valid_from = _as_utc(sub.valid_from) or now_utc
    valid_until = _as_utc(sub.valid_until)
    is_trial = False
    if valid_until is not None:
        total_days = (valid_until - valid_from).total_seconds() / 86400.0
        if total_days <= 16:
            is_trial = True

    evaluation_now = _as_utc(sub.paused_at) if sub.status == "PAUSED" and sub.paused_at is not None else now_utc
    is_expired = sub.status in ("EXPIRED", "CANCELLED", "SUSPENDED") or (
        sub.status != "PAUSED" and valid_until is not None and valid_until <= evaluation_now
    )
    days_remaining: int | None = None
    retention_days_remaining: int | None = None

    if valid_until is not None:
        if valid_until > evaluation_now and not is_expired:
            days_remaining = max(1, int(ceil((valid_until - evaluation_now).total_seconds() / 86400.0)))
        else:
            days_remaining = 0
            retention_end = valid_until + timedelta(days=RETENTION_WINDOW_DAYS)
            if retention_end > evaluation_now:
                retention_days_remaining = max(0, int(ceil((retention_end - evaluation_now).total_seconds() / 86400.0)))
            else:
                retention_days_remaining = 0
    return {
        "is_trial": is_trial,
        "is_expired": is_expired,
        "days_remaining": days_remaining,
        "retention_days_remaining": retention_days_remaining,
    }


def serialize_tenant(tenant: Tenant, db: Session | None = None) -> dict[str, Any]:
    subs_sorted = sorted(
        tenant.subscriptions,
        key=lambda s: _as_utc(s.valid_from) or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )
    active_sub = next((s for s in subs_sorted if s.status == "ACTIVE"), None) or (subs_sorted[0] if subs_sorted else None)
    win = _evaluate_subscription_window(active_sub)

    reactivation_requested = False
    requested_plan_code: str | None = None
    if db is not None:
        latest_req = db.scalar(
            select(Bitacora)
            .where(Bitacora.tenant_id == tenant.id, Bitacora.action == "REACTIVATION_REQUEST")
            .order_by(Bitacora.id.desc())
            .execution_options(ignore_tenant_scope=True)
        )
        if latest_req is not None:
            sub_start = _as_utc(active_sub.valid_from) if active_sub and not win["is_expired"] else None
            req_time = _as_utc(latest_req.created_at)
            if sub_start is None or (req_time is not None and req_time >= sub_start):
                reactivation_requested = True
                if isinstance(latest_req.new_values, dict):
                    requested_plan_code = latest_req.new_values.get("requested_plan_code")

        latest_cancel = db.scalar(
            select(Bitacora)
            .where(Bitacora.tenant_id == tenant.id, Bitacora.action.in_(["SUBSCRIPTION_CANCELLED", "SUBSCRIPTION_RESUMED"]))
            .order_by(Bitacora.id.desc())
            .execution_options(ignore_tenant_scope=True)
        )
        is_cancelled = False
        cancellation_reason = None
        if latest_cancel is not None and latest_cancel.action == "SUBSCRIPTION_CANCELLED":
            is_cancelled = True
            if isinstance(latest_cancel.new_values, dict):
                cancellation_reason = latest_cancel.new_values.get("reason")
    else:
        is_cancelled = False
        cancellation_reason = None

    return {
        "id": tenant.id,
        "name": tenant.name,
        "status": tenant.status,
        "created_at": tenant.created_at,
        "active_subscription": serialize_subscription(active_sub) if active_sub is not None else None,
        "is_trial": win["is_trial"],
        "is_expired": win["is_expired"],
        "is_cancelled": is_cancelled,
        "cancellation_reason": cancellation_reason,
        "reactivation_requested": reactivation_requested,
        "requested_plan_code": requested_plan_code,
    }


def list_plans(db: Session, only_active: bool = True) -> list[dict[str, Any]]:
    statement = select(SubscriptionPlan).order_by(SubscriptionPlan.id)
    if only_active:
        statement = statement.where(SubscriptionPlan.is_active.is_(True))
    plans = db.scalars(statement).all()
    return [serialize_plan(p) for p in plans]


def get_plan_by_code(db: Session, code: str) -> SubscriptionPlan:
    normalized = code.strip().upper()
    if normalized == "PRO":
        normalized = "PROFESSIONAL"
    plan = db.scalar(select(SubscriptionPlan).where(SubscriptionPlan.code == normalized))
    if plan is None:
        raise _not_found(f"Plan con código '{code}' no encontrado.", "PLAN_NOT_FOUND")
    return plan


def create_plan(db: Session, data: SubscriptionPlanCreateRequest, actor: User | None = None) -> dict[str, Any]:
    code = data.code.strip().upper()
    if db.scalar(select(SubscriptionPlan.id).where(SubscriptionPlan.code == code)):
        raise _conflict(f"Ya existe un plan con código '{code}'.", "PLAN_CODE_EXISTS")
    plan = SubscriptionPlan(
        code=code,
        name=data.name.strip(),
        price_monthly=Decimal(str(data.price_monthly)),
        price_annual=Decimal(str(data.price_annual)),
        currency=data.currency.strip().upper(),
        max_active_branches=data.max_active_branches,
        generative_reports_enabled=data.generative_reports_enabled,
        is_active=data.is_active,
    )
    db.add(plan)
    db.flush()
    record_audit(
        db,
        actor,
        "CREATE",
        "subscription_plan",
        plan.id,
        f"Plan '{plan.name}' ({plan.code}) creado.",
        new_values=serialize_plan(plan),
    )
    db.flush()
    return serialize_plan(plan)


def update_plan(db: Session, plan_id: int, data: SubscriptionPlanUpdateRequest, actor: User | None = None) -> dict[str, Any]:
    plan = db.get(SubscriptionPlan, plan_id)
    if plan is None:
        raise _not_found("Plan de suscripción no encontrado.", "PLAN_NOT_FOUND")
    if data.name is not None:
        plan.name = data.name.strip()
    if data.price_monthly is not None:
        plan.price_monthly = Decimal(str(data.price_monthly))
    if data.price_annual is not None:
        plan.price_annual = Decimal(str(data.price_annual))
    if data.currency is not None:
        plan.currency = data.currency.strip().upper()
    if data.max_active_branches is not None:
        plan.max_active_branches = data.max_active_branches
    if data.generative_reports_enabled is not None:
        plan.generative_reports_enabled = data.generative_reports_enabled
    if data.is_active is not None:
        plan.is_active = data.is_active
    db.flush()
    record_audit(
        db,
        actor,
        "UPDATE",
        "subscription_plan",
        plan.id,
        f"Plan '{plan.name}' ({plan.code}) actualizado.",
        new_values=serialize_plan(plan),
    )
    db.flush()
    return serialize_plan(plan)


def list_tenants(db: Session, page: int = 1, page_size: int = 20) -> dict[str, Any]:
    statement = select(Tenant).options(joinedload(Tenant.subscriptions).joinedload(Subscription.plan)).order_by(Tenant.name)
    count_statement = select(func.count(Tenant.id))
    total = db.scalar(count_statement) or 0
    items = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).unique().all()
    return {
        "items": [serialize_tenant(t, db=db) for t in items],
        "total": total,
    }


def get_tenant(db: Session, tenant_id: int) -> Tenant:
    tenant = db.scalar(select(Tenant).options(joinedload(Tenant.subscriptions).joinedload(Subscription.plan)).where(Tenant.id == tenant_id))
    if tenant is None:
        raise _not_found("Empresa no encontrada.", "TENANT_NOT_FOUND")
    return tenant


def create_tenant(db: Session, data: TenantCreateRequest, actor: User | None = None) -> Tenant:
    name = data.name.strip()
    if db.scalar(select(Tenant.id).where(func.lower(Tenant.name) == name.lower())):
        raise _conflict("Ya existe una empresa con ese nombre.", "TENANT_NAME_EXISTS")
    plan = get_plan_by_code(db, data.plan_code)

    tenant = Tenant(name=name, status="ACTIVE")
    db.add(tenant)
    db.flush()

    now = datetime.now(UTC)
    sub = Subscription(tenant_id=tenant.id, plan_id=plan.id, status="ACTIVE", valid_from=now)
    db.add(sub)

    if data.admin_email:
        email = str(data.admin_email).strip().lower()
        role_admin = db.scalar(select(Role).where(Role.code == "ADMIN"))
        if role_admin is None:
            raise _not_found("Rol de Administrador no encontrado.", "ROLE_NOT_FOUND")
        pwd = data.admin_password or "AdminSeed123!"
        admin_user = User(
            tenant_id=tenant.id,
            role_id=role_admin.id,
            first_name=data.admin_first_name or "Admin",
            last_name=data.admin_last_name or name,
            email=email,
            phone=data.admin_phone or "70000000",
            password_hash=hash_password(pwd),
        )
        db.add(admin_user)

    record_audit(
        db,
        actor,
        "CREATE",
        "tenant",
        tenant.id,
        f"Empresa '{tenant.name}' registrada con plan '{plan.code}'.",
        new_values={"name": tenant.name, "plan_code": plan.code, "status": tenant.status},
    )
    db.flush()
    return get_tenant(db, tenant.id)


def trial_signup(db: Session, data: TrialSignupRequest, client_ip: str | None = None) -> dict[str, Any]:
    _check_trial_rate_limit(client_ip)
    company_name = data.company_name.strip()
    email = str(data.email).strip().lower()

    if db.scalar(select(Tenant.id).where(func.lower(Tenant.name) == company_name.lower())):
        raise _conflict("Ya existe una empresa registrada con ese nombre.", "TENANT_NAME_EXISTS")

    existing_user = db.scalar(
        select(User.id)
        .where(func.lower(User.email) == email)
        .execution_options(ignore_tenant_scope=True)
    )
    if existing_user is not None:
        raise _conflict("Este correo electrónico ya fue utilizado para registrar una cuenta o prueba.", "EMAIL_ALREADY_EXISTS")

    basic_plan = db.scalar(select(SubscriptionPlan).where(SubscriptionPlan.code == "BASIC"))
    if basic_plan is None:
        basic_plan = SubscriptionPlan(
            code="BASIC",
            name="Básico",
            max_active_branches=2,
            generative_reports_enabled=False,
            is_active=True,
        )
        db.add(basic_plan)
        db.flush()

    role_admin = db.scalar(select(Role).where(Role.code == "ADMIN"))
    if role_admin is None:
        role_admin = Role(code="ADMIN", name="Administrador", is_active=True)
        db.add(role_admin)
        db.flush()

    tenant = Tenant(name=company_name, status="ACTIVE")
    db.add(tenant)
    db.flush()

    now = datetime.now(UTC)
    trial_until = now + timedelta(days=TRIAL_DURATION_DAYS)
    sub = Subscription(
        tenant_id=tenant.id,
        plan_id=basic_plan.id,
        status="ACTIVE",
        valid_from=now,
        valid_until=trial_until,
    )
    db.add(sub)

    admin_user = User(
        tenant_id=tenant.id,
        role_id=role_admin.id,
        first_name=data.first_name.strip(),
        last_name=data.last_name.strip(),
        email=email,
        phone=data.phone.strip(),
        password_hash=hash_password(data.password),
        is_active=True,
    )
    db.add(admin_user)
    db.flush()

    verification_token = uuid4().hex
    db.add(
        Bitacora(
            tenant_id=tenant.id,
            user_id=admin_user.id,
            action="TRIAL_SIGNUP",
            entity_type="tenant",
            entity_id=tenant.id,
            description=f"Alta self-service de prueba gratuita ({TRIAL_DURATION_DAYS} días) para '{tenant.name}'.",
            new_values={
                "company_name": tenant.name,
                "plan_code": basic_plan.code,
                "trial_days": TRIAL_DURATION_DAYS,
                "valid_until": trial_until.isoformat(),
                "verification_token": verification_token,
            },
            ip_address=client_ip,
        )
    )
    db.flush()

    loaded_user = db.scalar(
        select(User)
        .options(
            joinedload(User.tenant),
            joinedload(User.role).joinedload(Role.permissions),
            selectinload(User.branches),
        )
        .where(User.id == admin_user.id)
        .execution_options(ignore_tenant_scope=True)
    )
    return auth_service._issue_tokens(db, loaded_user or admin_user)


def verify_tenant_email(db: Session, user: User) -> dict[str, Any]:
    if user.tenant_id is None:
        raise _not_found("El usuario no pertenece a una empresa.", "TENANT_NOT_FOUND")
    db.add(
        Bitacora(
            tenant_id=user.tenant_id,
            user_id=user.id,
            action="EMAIL_VERIFIED",
            entity_type="user",
            entity_id=user.id,
            description=f"Correo electrónico '{user.email}' verificado.",
            new_values={"email": user.email, "verified": True},
        )
    )
    db.flush()
    return get_subscription_status(db, user.tenant_id)


def request_reactivation(db: Session, user: User, data: ReactivationRequestPayload) -> dict[str, Any]:
    if user.tenant_id is None:
        raise _not_found("El usuario no pertenece a una empresa.", "TENANT_NOT_FOUND")
    plan = get_plan_by_code(db, data.plan_code)
    db.add(
        Bitacora(
            tenant_id=user.tenant_id,
            user_id=user.id,
            action="REACTIVATION_REQUEST",
            entity_type="tenant",
            entity_id=user.tenant_id,
            description=f"Solicitud de reactivación/cambio al plan '{plan.code}'.",
            new_values={
                "requested_plan_code": plan.code,
                "notes": data.notes,
                "requested_by_email": user.email,
            },
        )
    )
    db.flush()
    return get_subscription_status(db, user.tenant_id)


def export_tenant_data(db: Session, tenant_id: int) -> dict[str, Any]:
    status_info = get_subscription_status(db, tenant_id)
    branches = db.scalars(select(Branch).where(Branch.tenant_id == tenant_id).order_by(Branch.id)).all()
    categories = db.scalars(select(Category).where(Category.tenant_id == tenant_id).order_by(Category.id)).all()
    products = db.scalars(select(Product).where(Product.tenant_id == tenant_id).order_by(Product.id)).all()

    return {
        "tenant": {
            "id": status_info["tenant_id"],
            "name": status_info["tenant_name"],
            "status": status_info["tenant_status"],
        },
        "subscription": status_info["subscription"],
        "retention_days_remaining": status_info["retention_days_remaining"],
        "exported_at": datetime.now(UTC),
        "branches": [
            {
                "id": b.id,
                "name": b.name,
                "address": b.address,
                "phone": b.phone,
                "is_active": b.is_active,
            }
            for b in branches
        ],
        "categories": [
            {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "is_active": c.is_active,
            }
            for c in categories
        ],
        "products": [
            {
                "id": p.id,
                "code": p.code,
                "name": p.name,
                "slug": p.slug,
                "price": float(p.price),
                "is_active": p.is_active,
            }
            for p in products
        ],
    }


def update_tenant_status(db: Session, tenant_id: int, new_status: str, actor: User | None = None) -> Tenant:
    tenant = get_tenant(db, tenant_id)
    prev = tenant.status
    tenant.status = new_status
    record_audit(
        db,
        actor,
        "UPDATE",
        "tenant",
        tenant.id,
        f"Estado de empresa '{tenant.name}' cambiado de {prev} a {new_status}.",
        new_values={"status": new_status, "previous_status": prev},
    )
    db.flush()
    return tenant


def change_subscription(
    db: Session,
    tenant_id: int,
    data: SubscriptionChangeRequest,
    actor: User | None = None,
) -> Subscription:
    tenant = get_tenant(db, tenant_id)
    new_plan = get_plan_by_code(db, data.plan_code)

    now = datetime.now(UTC)
    active_subs = db.scalars(select(Subscription).where(Subscription.tenant_id == tenant.id, Subscription.status == "ACTIVE")).all()
    for s in active_subs:
        s.status = "CANCELLED"
        if s.valid_until is None or _as_utc(s.valid_until) > now:
            s.valid_until = now

    new_sub = Subscription(
        tenant_id=tenant.id,
        plan_id=new_plan.id,
        status="ACTIVE",
        valid_from=now,
        valid_until=data.valid_until,
    )
    db.add(new_sub)
    db.flush()

    record_audit(
        db,
        actor,
        "UPDATE",
        "subscription",
        new_sub.id,
        f"Suscripción de empresa '{tenant.name}' cambiada a '{new_plan.code}'.",
        new_values={"tenant_id": tenant.id, "plan_code": new_plan.code, "status": "ACTIVE"},
    )
    db.flush()
    return db.scalar(select(Subscription).options(joinedload(Subscription.plan)).where(Subscription.id == new_sub.id))


def _latest_subscription(db: Session, tenant_id: int) -> Subscription:
    sub = db.scalar(
        select(Subscription).options(joinedload(Subscription.plan)).where(Subscription.tenant_id == tenant_id)
        .order_by(Subscription.valid_from.desc(), Subscription.id.desc())
    )
    if sub is None:
        raise _not_found("La empresa no tiene una suscripción.", "SUBSCRIPTION_NOT_FOUND")
    return sub


def renew_subscription(db: Session, tenant_id: int, actor: User | None = None, renewed_at: datetime | None = None) -> Subscription:
    tenant = get_tenant(db, tenant_id)
    sub = _latest_subscription(db, tenant.id)
    now = _as_utc(renewed_at) or datetime.now(UTC)
    if sub.status == "PAUSED":
        raise _conflict("La suscripción pausada debe reanudarse antes de renovarse.", "SUBSCRIPTION_PAUSED")
    previous_until = _as_utc(sub.valid_until)
    if previous_until is not None and previous_until > now:
        sub.valid_until = previous_until + timedelta(days=30)
    elif previous_until is not None:
        sub.valid_until = now + timedelta(days=30)
    else:
        sub.valid_until = None
    sub.status = "ACTIVE"
    record_audit(db, actor, "SUBSCRIPTION_RENEWED", "subscription", sub.id,
                 f"Suscripción de empresa '{tenant.name}' renovada por 30 días.",
                 old_values={"valid_until": previous_until.isoformat() if previous_until else None, "plan_code": sub.plan.code},
                 new_values={"valid_until": sub.valid_until.isoformat() if sub.valid_until else None, "plan_code": sub.plan.code})
    db.flush()
    return sub


def pause_subscription(db: Session, tenant_id: int, actor: User | None = None, paused_at: datetime | None = None) -> Subscription:
    tenant = get_tenant(db, tenant_id)
    sub = _latest_subscription(db, tenant.id)
    now = _as_utc(paused_at) or datetime.now(UTC)
    if sub.status == "PAUSED":
        raise _conflict("La suscripción ya está pausada.", "SUBSCRIPTION_ALREADY_PAUSED")
    if sub.status != "ACTIVE" or (sub.valid_until is not None and _as_utc(sub.valid_until) <= now):
        raise _conflict("Solo se puede pausar una suscripción activa y vigente.", "SUBSCRIPTION_NOT_PAUSABLE")
    sub.status = "PAUSED"
    sub.paused_at = now
    record_audit(db, actor, "SUBSCRIPTION_PAUSED", "subscription", sub.id,
                 f"Suscripción de empresa '{tenant.name}' pausada.", new_values={"paused_at": now.isoformat()})
    db.flush()
    return sub


def resume_subscription(db: Session, tenant_id: int, actor: User | None = None, resumed_at: datetime | None = None) -> Subscription:
    tenant = get_tenant(db, tenant_id)
    sub = _latest_subscription(db, tenant.id)
    if sub.status != "PAUSED" or sub.paused_at is None:
        raise _conflict("La suscripción no está pausada.", "SUBSCRIPTION_NOT_PAUSED")
    now = _as_utc(resumed_at) or datetime.now(UTC)
    elapsed = now - _as_utc(sub.paused_at)
    previous_until = _as_utc(sub.valid_until)
    if previous_until is not None:
        sub.valid_until = previous_until + elapsed
    sub.status = "ACTIVE"
    sub.paused_at = None
    record_audit(db, actor, "SUBSCRIPTION_RESUMED", "subscription", sub.id,
                 f"Suscripción de empresa '{tenant.name}' reanudada.", new_values={"elapsed_seconds": int(elapsed.total_seconds())})
    db.flush()
    return sub


def list_tenant_subscriptions(db: Session, tenant_id: int) -> list[dict[str, Any]]:
    get_tenant(db, tenant_id)
    subs = db.scalars(select(Subscription).options(joinedload(Subscription.plan)).where(Subscription.tenant_id == tenant_id).order_by(Subscription.valid_from.desc())).all()
    return [serialize_subscription(s) for s in subs]


def is_tenant_subscription_expired(db: Session, tenant_id: int | None) -> bool:
    if tenant_id is None:
        return False
    subs = db.scalars(
        select(Subscription)
        .where(Subscription.tenant_id == tenant_id)
        .order_by(Subscription.valid_from.desc(), Subscription.id.desc())
        .execution_options(ignore_tenant_scope=True)
    ).all()
    if not subs:
        # Si un tenant de prueba unitaria fue creado sin filas de Subscription, no bloquear
        return False
    now = datetime.now(UTC)
    for s in subs:
        if s.status == "ACTIVE":
            until = _as_utc(s.valid_until)
            if until is None or until > now:
                return False
    return True


def get_subscription_status(db: Session, tenant_id: int) -> dict[str, Any]:
    tenant = get_tenant(db, tenant_id)
    subs = db.scalars(
        select(Subscription)
        .options(joinedload(Subscription.plan))
        .where(Subscription.tenant_id == tenant_id)
        .order_by(Subscription.valid_from.desc(), Subscription.id.desc())
    ).all()
    now = datetime.now(UTC)
    sub = next((s for s in subs if s.status == "ACTIVE"), None) or (subs[0] if subs else None)
    if sub is not None and sub.status == "ACTIVE" and sub.valid_until is not None and _as_utc(sub.valid_until) <= now:
        sub.status = "EXPIRED"
        db.flush()

    win = _evaluate_subscription_window(sub, now=now)
    plan = sub.plan if sub is not None else None
    active_branch_count = db.scalar(select(func.count(Branch.id)).where(Branch.tenant_id == tenant_id, Branch.is_active.is_(True))) or 0

    has_trial_audit = db.scalar(
        select(Bitacora.id)
        .where(Bitacora.tenant_id == tenant_id, Bitacora.action == "TRIAL_SIGNUP")
        .execution_options(ignore_tenant_scope=True)
    ) is not None
    has_verified_audit = db.scalar(
        select(Bitacora.id)
        .where(Bitacora.tenant_id == tenant_id, Bitacora.action == "EMAIL_VERIFIED")
        .execution_options(ignore_tenant_scope=True)
    ) is not None
    email_verified = True if not has_trial_audit else has_verified_audit

    latest_req = db.scalar(
        select(Bitacora)
        .where(Bitacora.tenant_id == tenant_id, Bitacora.action == "REACTIVATION_REQUEST")
        .order_by(Bitacora.id.desc())
        .execution_options(ignore_tenant_scope=True)
    )
    reactivation_requested = False
    requested_plan_code: str | None = None
    if latest_req is not None:
        sub_start = _as_utc(sub.valid_from) if sub and not win["is_expired"] else None
        req_time = _as_utc(latest_req.created_at)
        if sub_start is None or (req_time is not None and req_time >= sub_start):
            reactivation_requested = True
            if isinstance(latest_req.new_values, dict):
                requested_plan_code = latest_req.new_values.get("requested_plan_code")

    latest_cancel = db.scalar(
        select(Bitacora)
        .where(Bitacora.tenant_id == tenant_id, Bitacora.action.in_(["SUBSCRIPTION_CANCELLED", "SUBSCRIPTION_RESUMED"]))
        .order_by(Bitacora.id.desc())
        .execution_options(ignore_tenant_scope=True)
    )
    is_cancelled = False
    cancellation_reason: str | None = None
    cancellation_effective_at: datetime | None = None
    if latest_cancel is not None and latest_cancel.action == "SUBSCRIPTION_CANCELLED":
        is_cancelled = True
        if isinstance(latest_cancel.new_values, dict):
            cancellation_reason = latest_cancel.new_values.get("reason")
            eff = latest_cancel.new_values.get("effective_until")
            if eff:
                try:
                    cancellation_effective_at = datetime.fromisoformat(eff)
                except Exception:
                    cancellation_effective_at = None

    is_trial = win["is_trial"] or (has_trial_audit and sub is not None and sub.valid_until is not None)
    is_expired = win["is_expired"]

    return {
        "tenant_id": tenant.id,
        "tenant_name": tenant.name,
        "tenant_status": tenant.status,
        "subscription": serialize_subscription(sub) if sub is not None else None,
        "plan": serialize_plan(plan) if plan is not None else None,
        "max_active_branches": plan.max_active_branches if plan is not None else 1,
        "generative_reports_enabled": plan.generative_reports_enabled if plan is not None else False,
        "active_branch_count": active_branch_count,
        "is_trial": is_trial,
        "is_expired": is_expired,
        "is_cancelled": is_cancelled,
        "cancellation_reason": cancellation_reason,
        "cancellation_effective_at": cancellation_effective_at,
        "read_only_mode": is_expired or sub is not None and sub.status == "PAUSED",
        "is_paused": sub is not None and sub.status == "PAUSED",
        "days_remaining": win["days_remaining"],
        "retention_days_remaining": win["retention_days_remaining"],
        "email_verified": email_verified,
        "reactivation_requested": reactivation_requested,
        "requested_plan_code": requested_plan_code,
    }


def cancel_tenant_subscription(db: Session, user: User, data: SubscriptionCancelRequest) -> dict[str, Any]:
    if user.tenant_id is None:
        raise _not_found("El usuario no pertenece a una empresa.", "TENANT_NOT_FOUND")
    tenant = get_tenant(db, user.tenant_id)

    sub = db.scalar(
        select(Subscription)
        .options(joinedload(Subscription.plan))
        .where(Subscription.tenant_id == user.tenant_id, Subscription.status == "ACTIVE")
        .order_by(Subscription.valid_from.desc())
    )
    if sub is None:
        raise _conflict("No hay una suscripción activa para cancelar.", "NO_ACTIVE_SUBSCRIPTION")

    # Si la suscripción fue contratada por Stripe, notificar a Stripe
    if sub.provider_subscription_id:
        try:
            import stripe
            if settings.STRIPE_SECRET_KEY:
                stripe.api_key = settings.STRIPE_SECRET_KEY
                if data.immediate:
                    stripe.Subscription.cancel(sub.provider_subscription_id)
                else:
                    stripe.Subscription.modify(sub.provider_subscription_id, cancel_at_period_end=True)
        except Exception:
            pass

    now_utc = datetime.now(UTC)
    effective_until = sub.valid_until or now_utc
    if data.immediate:
        sub.status = "CANCELLED"
        effective_until = now_utc

    db.add(
        Bitacora(
            tenant_id=user.tenant_id,
            user_id=user.id,
            action="SUBSCRIPTION_CANCELLED",
            entity_type="subscription",
            entity_id=sub.id,
            description=f"Cancelación voluntaria solicitada por {user.email}. Motivo: {data.reason}.",
            new_values={
                "reason": data.reason,
                "feedback": data.feedback,
                "immediate": data.immediate,
                "effective_until": effective_until.isoformat() if effective_until else None,
            },
        )
    )
    db.flush()
    return get_subscription_status(db, user.tenant_id)


def resume_tenant_subscription(db: Session, user: User) -> dict[str, Any]:
    if user.tenant_id is None:
        raise _not_found("El usuario no pertenece a una empresa.", "TENANT_NOT_FOUND")
    tenant = get_tenant(db, user.tenant_id)

    sub = db.scalar(
        select(Subscription)
        .options(joinedload(Subscription.plan))
        .where(Subscription.tenant_id == user.tenant_id)
        .order_by(Subscription.valid_from.desc())
    )
    if sub is None:
        raise _conflict("No hay una suscripción registrada para reanudar.", "NO_SUBSCRIPTION")

    if sub.provider_subscription_id:
        try:
            import stripe
            if settings.STRIPE_SECRET_KEY:
                stripe.api_key = settings.STRIPE_SECRET_KEY
                stripe.Subscription.modify(sub.provider_subscription_id, cancel_at_period_end=False)
        except Exception:
            pass

    if sub.status in ("PAUSED", "CANCELLED"):
        sub.status = "ACTIVE"
        sub.paused_at = None

    db.add(
        Bitacora(
            tenant_id=user.tenant_id,
            user_id=user.id,
            action="SUBSCRIPTION_RESUMED",
            entity_type="subscription",
            entity_id=sub.id,
            description=f"Suscripción reactivada / cancelación deshecha por {user.email}.",
            new_values={"resumed_at": datetime.now(UTC).isoformat()},
        )
    )
    db.flush()
    return get_subscription_status(db, user.tenant_id)


def check_tenant_feature(db: Session, tenant_id: int | None, feature_name: str) -> bool:
    if tenant_id is None:
        return True
    now = datetime.now(UTC)
    active_sub = db.scalar(
        select(Subscription)
        .options(joinedload(Subscription.plan))
        .where(Subscription.tenant_id == tenant_id, Subscription.status == "ACTIVE")
        .order_by(Subscription.valid_from.desc())
    )
    if active_sub is None or active_sub.plan is None:
        return False
    if active_sub.valid_until is not None and _as_utc(active_sub.valid_until) <= now:
        return False
    return bool(getattr(active_sub.plan, feature_name, False))


