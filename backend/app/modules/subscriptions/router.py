from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.models import Tenant, User
from app.modules.auth.dependencies import (
    get_current_user,
    require_admin,
    require_platform_permission,
    resolve_platform_target_tenant,
)
from app.modules.auth.schemas import AuthResponse
from app.modules.subscriptions import service, stripe_service
from app.modules.subscriptions.schemas import (
    EmailVerificationStartRequest,
    EmailVerificationStartResponse,
    EmailVerificationVerifyRequest,
    EmailVerificationVerifyResponse,
    PaidCheckoutRequest,
    PaidCheckoutResponse,
    PaidCheckoutStatusResponse,
    ReactivationRequestPayload,
    SubscriptionCancelRequest,
    SubscriptionChangeRequest,
    SubscriptionCurrentResponse,
    SubscriptionHistoryPage,
    SubscriptionPlanCreateRequest,
    SubscriptionPlanPage,
    SubscriptionPlanResponse,
    SubscriptionPlanUpdateRequest,
    SubscriptionResponse,
    TenantCreateRequest,
    TenantExportResponse,
    TenantPage,
    TenantResponse,
    TenantStatusUpdateRequest,
    TrialSignupRequest,
)

router = APIRouter(tags=["subscriptions"])
platform_router = APIRouter(prefix="/platform", tags=["platform-saas"])


# --- Public / Tenant operational routes ---


@router.post("/subscriptions/email-verification/start", response_model=EmailVerificationStartResponse)
def start_email_verification(data: EmailVerificationStartRequest, db: Session = Depends(get_db)):
    result = service.create_email_verification(db, str(data.email))
    db.commit()
    return result


@router.post("/subscriptions/email-verification/verify", response_model=EmailVerificationVerifyResponse)
def verify_email_verification(data: EmailVerificationVerifyRequest, db: Session = Depends(get_db)):
    result = service.verify_email_code(db, str(data.email), data.code)
    db.commit()
    return result


@router.get("/plans", response_model=SubscriptionPlanPage)
def list_active_plans(db: Session = Depends(get_db)):
    """Consulta pública / autenticada de planes de suscripción activos."""
    items = service.list_plans(db, only_active=True)
    return {"items": items, "total": len(items)}


@router.post("/subscriptions/paid-checkout", response_model=PaidCheckoutResponse, status_code=status.HTTP_201_CREATED)
def create_paid_checkout_session(
    data: PaidCheckoutRequest,
    db: Session = Depends(get_db),
):
    """Create a pending paid registration and a hosted recurring Stripe session."""
    result = service.create_paid_checkout(db, data)
    db.commit()
    return result


@router.get("/subscriptions/paid-checkout/status", response_model=PaidCheckoutStatusResponse)
def get_paid_checkout_status(
    response: Response,
    session_id: str = Query(..., min_length=1, max_length=255),
    db: Session = Depends(get_db),
):
    """Return only the local coarse state; webhook processing grants access."""
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return service.get_paid_checkout_status(db, session_id)


@router.post("/subscriptions/stripe/webhook")
async def stripe_subscription_webhook(
    request: Request,
    db: Session = Depends(get_db),
    stripe_signature: str | None = Header(default=None, alias="stripe-signature"),
):
    """Unauthenticated Stripe endpoint; signature verification is mandatory and fail-closed."""
    payload = await request.body()
    result = stripe_service.handle_webhook(db, payload, stripe_signature)
    db.commit()
    return result


@router.post("/subscriptions/trial-signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register_company_trial(
    data: TrialSignupRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Alta self-service de empresa con acceso inmediato y prueba de 14 días sin tarjeta."""
    client_ip = request.client.host if request.client else None
    result = service.trial_signup(db, data, client_ip=client_ip)
    db.commit()
    return result


@router.get("/subscriptions/current", response_model=SubscriptionCurrentResponse)
def get_my_subscription_status(
    current_user: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    """Consulta del estado y vigencia de la suscripción de la empresa actual."""
    result = service.get_subscription_status(db, current_user.tenant_id)
    db.commit()
    return result


@router.post("/subscriptions/verify-email", response_model=SubscriptionCurrentResponse)
def verify_my_company_email(
    current_user: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    """Confirmar verificación de correo de la empresa en prueba."""
    result = service.verify_tenant_email(db, current_user)
    db.commit()
    return result


@router.post("/subscriptions/reactivation-request", response_model=SubscriptionCurrentResponse)
def request_subscription_reactivation(
    data: ReactivationRequestPayload,
    current_user: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    """Solicitar reactivación o cambio de plan desde la cuenta de la empresa."""
    result = service.request_reactivation(db, current_user, data)
    db.commit()
    return result


@router.get("/subscriptions/export", response_model=TenantExportResponse)
def export_my_company_data(
    current_user: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    """Exportar los datos de la empresa (permitido durante la prueba y los 90 días posteriores al vencimiento)."""
    return service.export_tenant_data(db, current_user.tenant_id)


@router.post("/subscriptions/cancel", response_model=SubscriptionCurrentResponse)
def cancel_my_subscription(
    data: SubscriptionCancelRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    """Cancelación voluntaria self-service de suscripción iniciada por el administrador de la empresa."""
    result = service.cancel_tenant_subscription(db, current_user, data)
    db.commit()
    return result


@router.post("/subscriptions/resume", response_model=SubscriptionCurrentResponse)
def resume_my_subscription(
    current_user: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    """Reactivar suscripción / revertir la cancelación voluntaria mientras siga en período de gracia o vigencia."""
    result = service.resume_tenant_subscription(db, current_user)
    db.commit()
    return result


# --- Platform Admin routes ---


@platform_router.get("/plans", response_model=SubscriptionPlanPage)
def list_all_platform_plans(
    _: Annotated[User, Depends(require_platform_permission("saas.plans.manage"))],
    db: Session = Depends(get_db),
):
    """Listado completo de planes para administración SaaS."""
    items = service.list_plans(db, only_active=False)
    return {"items": items, "total": len(items)}


@platform_router.post("/plans", response_model=SubscriptionPlanResponse, status_code=status.HTTP_201_CREATED)
def create_platform_plan(
    data: SubscriptionPlanCreateRequest,
    actor: Annotated[User, Depends(require_platform_permission("saas.plans.manage"))],
    db: Session = Depends(get_db),
):
    """Crear un nuevo plan de suscripción SaaS."""
    plan = service.create_plan(db, data, actor=actor)
    db.commit()
    return plan


@platform_router.patch("/plans/{plan_id}", response_model=SubscriptionPlanResponse)
def update_platform_plan(
    plan_id: int,
    data: SubscriptionPlanUpdateRequest,
    actor: Annotated[User, Depends(require_platform_permission("saas.plans.manage"))],
    db: Session = Depends(get_db),
):
    """Actualizar límites o estado de un plan de suscripción SaaS."""
    plan = service.update_plan(db, plan_id, data, actor=actor)
    db.commit()
    return plan


@platform_router.post("/tenants", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
def register_tenant(
    data: TenantCreateRequest,
    actor: Annotated[User, Depends(require_platform_permission("saas.tenants.manage"))],
    db: Session = Depends(get_db),
):
    """Registrar una nueva empresa cliente con su plan de suscripción inicial."""
    tenant = service.create_tenant(db, data, actor=actor)
    db.commit()
    return service.serialize_tenant(tenant, db=db)


@platform_router.get("/tenants", response_model=TenantPage)
def list_all_tenants(
    _: Annotated[User, Depends(require_platform_permission("saas.tenants.manage"))],
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """Listado de empresas registradas en la plataforma."""
    return service.list_tenants(db, page=page, page_size=page_size)


@platform_router.get("/tenants/{target_tenant_id}", response_model=TenantResponse)
def get_tenant_details(
    target_tenant: Annotated[Tenant, Depends(resolve_platform_target_tenant("saas.tenants.manage"))],
    db: Session = Depends(get_db),
):
    """Detalle de una empresa objetivo auditada."""
    return service.serialize_tenant(target_tenant, db=db)


@platform_router.patch("/tenants/{target_tenant_id}/status", response_model=TenantResponse)
def update_tenant_status(
    target_tenant: Annotated[Tenant, Depends(resolve_platform_target_tenant("saas.tenants.manage"))],
    data: TenantStatusUpdateRequest,
    actor: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Actualizar estado (ACTIVE, SUSPENDED, INACTIVE) de una empresa."""
    tenant = service.update_tenant_status(db, target_tenant.id, data.status, actor=actor)
    db.commit()
    return service.serialize_tenant(tenant, db=db)


@platform_router.post("/tenants/{target_tenant_id}/subscriptions", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def assign_or_change_subscription(
    target_tenant: Annotated[Tenant, Depends(resolve_platform_target_tenant("saas.subscriptions.manage"))],
    data: SubscriptionChangeRequest,
    actor: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Asignar o cambiar plan de suscripción para una empresa."""
    sub = service.change_subscription(db, target_tenant.id, data, actor=actor)
    db.commit()
    return service.serialize_subscription(sub)


@platform_router.post("/tenants/{target_tenant_id}/subscriptions/renew", response_model=SubscriptionResponse)
def renew_platform_subscription(
    target_tenant: Annotated[Tenant, Depends(resolve_platform_target_tenant("saas.subscriptions.manage"))],
    actor: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    sub = service.renew_subscription(db, target_tenant.id, actor=actor)
    db.commit()
    return service.serialize_subscription(sub)


@platform_router.post("/tenants/{target_tenant_id}/subscriptions/pause", response_model=SubscriptionResponse)
def pause_platform_subscription(
    target_tenant: Annotated[Tenant, Depends(resolve_platform_target_tenant("saas.subscriptions.manage"))],
    actor: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    sub = service.pause_subscription(db, target_tenant.id, actor=actor)
    db.commit()
    return service.serialize_subscription(sub)


@platform_router.post("/tenants/{target_tenant_id}/subscriptions/resume", response_model=SubscriptionResponse)
def resume_platform_subscription(
    target_tenant: Annotated[Tenant, Depends(resolve_platform_target_tenant("saas.subscriptions.manage"))],
    actor: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    sub = service.resume_subscription(db, target_tenant.id, actor=actor)
    db.commit()
    return service.serialize_subscription(sub)


@platform_router.get("/tenants/{target_tenant_id}/subscriptions", response_model=SubscriptionHistoryPage)
def list_subscription_history(
    target_tenant: Annotated[Tenant, Depends(resolve_platform_target_tenant("saas.subscriptions.manage"))],
    db: Session = Depends(get_db),
):
    """Consultar historial de suscripciones de una empresa."""
    items = service.list_tenant_subscriptions(db, target_tenant.id)
    return {"items": items, "total": len(items)}

