from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, object_session, selectinload

from app.core.database import get_db
from app.core.models import Bitacora, Branch, RefreshToken, Role, Tenant, User
from app.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
DbSession = Annotated[Session, Depends(get_db)]

TENANT_ADMIN_ROLE = "ADMIN"
PLATFORM_ADMIN_ROLE = "PLATFORM_ADMIN"
PLATFORM_PERMISSIONS = frozenset(
    {
        "saas.tenants.manage",
        "saas.plans.manage",
        "saas.subscriptions.manage",
    }
)
EXPLICIT_PLATFORM_ROUTE_PREFIX = "/api/v1/platform"


def _is_explicit_platform_route(request: Request | None) -> bool:
    if request is None:
        return False
    return request.url.path.startswith(EXPLICIT_PLATFORM_ROUTE_PREFIX) or bool(
        getattr(request.state, "is_platform_route", False)
    )


def _reject_untrusted_client_tenant_override(request: Request | None, user: User) -> None:
    if request is None:
        return
    raw_candidates = [
        request.headers.get("x-tenant-id"),
        request.headers.get("x-target-tenant-id"),
        request.query_params.get("tenant_id"),
        request.query_params.get("target_tenant_id"),
    ]
    has_override_candidate = any(raw_val is not None and str(raw_val).strip() != "" for raw_val in raw_candidates)
    if not has_override_candidate:
        return

    if user.role.code == PLATFORM_ADMIN_ROLE:
        if not _is_explicit_platform_route(request):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "CROSS_TENANT_PLATFORM_ROUTE_REQUIRED",
                    "message": "Las operaciones cross-tenant están reservadas exclusivamente para rutas explícitas de plataforma.",
                },
            )
        return

    for raw_val in raw_candidates:
        if raw_val is None or str(raw_val).strip() == "":
            continue
        try:
            requested_tid = int(str(raw_val).strip())
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "TENANT_SCOPE_FORBIDDEN", "message": "Identificador de empresa inválido o no autorizado."},
            ) from exc
        if user.tenant_id != requested_tid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "TENANT_SCOPE_FORBIDDEN", "message": "No tienes permiso para operar sobre otra empresa."},
            )


def bind_session_tenant_context(db: Session, user: User) -> None:
    if user.role.code == PLATFORM_ADMIN_ROLE:
        db.info["tenant_context_active"] = False
        db.info["tenant_id"] = None
        db.info["user_id"] = user.id
    else:
        db.info["tenant_context_active"] = True
        db.info["tenant_id"] = user.tenant_id
        db.info["user_id"] = user.id


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DbSession,
    request: Request = None,  # type: ignore[assignment]
) -> User:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado", headers={"WWW-Authenticate": "Bearer"})
    try:
        user_id = int(str(payload["sub"]))
        session_id = str(payload["jti"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido", headers={"WWW-Authenticate": "Bearer"}) from exc
    session = db.scalar(
        select(RefreshToken)
        .where(RefreshToken.session_id == session_id, RefreshToken.revoked_at.is_(None), RefreshToken.expires_at > datetime.now(UTC))
        .execution_options(ignore_tenant_scope=True)
    )
    user = db.scalar(
        select(User)
        .options(
            joinedload(User.tenant),
            joinedload(User.role).joinedload(Role.permissions),
            joinedload(User.supplier),
            selectinload(User.branches),
        )
        .where(User.id == user_id)
        .execution_options(ignore_tenant_scope=True)
    )
    if session is None or session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión inválida o cerrada", headers={"WWW-Authenticate": "Bearer"})
    if user is None or not user.is_active or not user.role.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no disponible", headers={"WWW-Authenticate": "Bearer"})
    if "tenant_id" in payload and payload.get("tenant_id") != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido para la empresa del usuario", headers={"WWW-Authenticate": "Bearer"})
    if user.tenant is not None and user.tenant.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "TENANT_INACTIVE", "message": "La empresa asociada al usuario no está activa."},
        )
    _reject_untrusted_client_tenant_override(request, user)
    if request is not None and user.tenant_id is not None and request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
        path = request.url.path
        allowed_when_expired = (
            path.startswith("/api/v1/auth/")
            or path.startswith("/api/v1/subscriptions/verify-email")
            or path.startswith("/api/v1/subscriptions/reactivation-request")
            or path.startswith("/api/v1/subscriptions/export")
        )
        if not allowed_when_expired:
            from app.modules.subscriptions.service import is_tenant_subscription_expired

            if is_tenant_subscription_expired(db, user.tenant_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "SUBSCRIPTION_EXPIRED",
                        "message": "Tu período de prueba o suscripción ha vencido. La cuenta está en modo consulta: puedes ver y exportar tus datos durante 90 días o solicitar la reactivación.",
                    },
                )
    bind_session_tenant_context(db, user)
    return user


def bind_optional_tenant_context(request: Request, db: DbSession) -> User | None:
    auth_header = request.headers.get("authorization")
    if not auth_header:
        return None
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return get_current_user(token=token.strip(), db=db, request=request)


def get_current_tenant_id(current_user: Annotated[User, Depends(get_current_user)]) -> int | None:
    return current_user.tenant_id


def get_current_tenant(current_user: Annotated[User, Depends(get_current_user)]) -> Tenant:
    if current_user.tenant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "TENANT_CONTEXT_REQUIRED", "message": "El usuario autenticado no pertenece a una empresa."},
        )
    return current_user.tenant


def require_platform_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if current_user.role.code != PLATFORM_ADMIN_ROLE or current_user.tenant_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PLATFORM_ADMIN_REQUIRED", "message": "Se requiere el rol de administrador de plataforma SaaS."},
        )
    return current_user


def require_platform_permission(permission_code: str):
    if permission_code not in PLATFORM_PERMISSIONS:
        raise ValueError(f"El permiso '{permission_code}' no es un permiso válido de plataforma SaaS.")

    def dependency(current_user: Annotated[User, Depends(require_platform_admin)]) -> User:
        role_perms = current_user.role.permissions
        if role_perms:
            has_active_perm = any(p.code == permission_code and p.is_active for p in role_perms)
            if not has_active_perm:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "PLATFORM_PERMISSION_REQUIRED",
                        "message": "No tienes el permiso de plataforma requerido para esta operación.",
                    },
                )
        return current_user

    return dependency


def resolve_platform_target_tenant(permission_code: str):
    if permission_code not in PLATFORM_PERMISSIONS:
        raise ValueError(f"El permiso '{permission_code}' no es un permiso válido de plataforma SaaS.")

    def dependency(
        request: Request,
        db: DbSession,
        current_user: Annotated[User, Depends(require_platform_permission(permission_code))],
    ) -> Tenant:
        if not _is_explicit_platform_route(request):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "CROSS_TENANT_PLATFORM_ROUTE_REQUIRED",
                    "message": "Las operaciones cross-tenant están reservadas exclusivamente para rutas explícitas de plataforma.",
                },
            )
        raw_target = (
            request.path_params.get("target_tenant_id")
            or request.path_params.get("tenant_id")
            or request.query_params.get("target_tenant_id")
            or request.query_params.get("tenant_id")
            or request.headers.get("x-target-tenant-id")
            or request.headers.get("x-tenant-id")
        )
        if raw_target is None or str(raw_target).strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "TARGET_TENANT_REQUIRED",
                    "message": "La operación de plataforma requiere declarar explícitamente el tenant objetivo.",
                },
            )
        try:
            target_tenant_id = int(str(raw_target).strip())
            if target_tenant_id <= 0:
                raise ValueError("target_tenant_id must be positive")
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "TARGET_TENANT_REQUIRED",
                    "message": "Identificador de tenant objetivo inválido.",
                },
            ) from exc

        target_tenant = db.get(Tenant, target_tenant_id)
        if target_tenant is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "TENANT_NOT_FOUND", "message": "La empresa objetivo no existe."},
            )

        db.add(
            Bitacora(
                tenant_id=target_tenant.id,
                user_id=current_user.id,
                action="PLATFORM_TARGET_ACCESS",
                entity_type="tenant",
                entity_id=target_tenant.id,
                description=f"Acceso de plataforma ({permission_code}) sobre empresa objetivo",
                new_values={
                    "actor_role": current_user.role.code,
                    "permission": permission_code,
                    "target_tenant_id": target_tenant.id,
                    "path": request.url.path,
                },
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
        )
        db.commit()
        return target_tenant

    return dependency


def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if current_user.role.code != TENANT_ADMIN_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ADMIN_ROLE_REQUIRED", "message": "Se requiere el rol ADMIN."},
        )
    return current_user


def require_permission(permission_code: str):
    if permission_code in PLATFORM_PERMISSIONS:
        return require_platform_permission(permission_code)

    def dependency(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role.code == PLATFORM_ADMIN_ROLE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "TENANT_OPERATION_FORBIDDEN_FOR_PLATFORM_ADMIN",
                    "message": "El administrador de plataforma no hereda acceso a operaciones internas de empresa.",
                },
            )
        if current_user.role.code == TENANT_ADMIN_ROLE or any(permission.code == permission_code and permission.is_active for permission in current_user.role.permissions):
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_REQUIRED", "message": "No tienes permisos para realizar esta operación."},
        )

    return dependency


def require_branch_access(
    current_user: Annotated[User, Depends(get_current_user)],
    branch_id: int,
) -> User:
    if current_user.role.code == PLATFORM_ADMIN_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "TENANT_OPERATION_FORBIDDEN_FOR_PLATFORM_ADMIN",
                "message": "El administrador de plataforma no tiene acceso a sucursales operativas.",
            },
        )
    session = object_session(current_user)
    if session is not None:
        tenant_cond = Branch.tenant_id.is_(None) if current_user.tenant_id is None else Branch.tenant_id == current_user.tenant_id
        branch = session.scalar(
            select(Branch).where(
                Branch.id == branch_id,
                tenant_cond,
            )
        )
        if branch is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BRANCH_NOT_FOUND", "message": "Sucursal no encontrada."},
            )
    if current_user.role.code != TENANT_ADMIN_ROLE and branch_id not in {branch.id for branch in current_user.branches}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "BRANCH_ACCESS_REQUIRED", "message": "No tienes acceso a esta sucursal."},
        )
    return current_user
