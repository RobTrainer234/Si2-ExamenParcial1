from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.models import RefreshToken, Role, User
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.core.config import settings
from app.modules.auth.schemas import RegisterRequest


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _user_response(user: User) -> dict[str, object]:
    branches = [
        {"id": b.id, "name": b.name}
        for b in (user.branches or [])
        if user.tenant_id is None or b.tenant_id is None or b.tenant_id == user.tenant_id
    ]
    tenant_summary = (
        {"id": user.tenant.id, "name": user.tenant.name, "status": user.tenant.status}
        if user.tenant is not None
        else None
    )
    return {
        "id": user.id,
        "tenant_id": user.tenant_id,
        "tenant": tenant_summary,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role.code,
        "is_active": user.is_active,
        "permissions": sorted(permission.code for permission in user.role.permissions if permission.is_active),
        "supplier_id": user.supplier_id,
        "branches": branches,
    }


def _issue_tokens(db: Session, user: User) -> dict[str, object]:
    refresh_token = create_refresh_token()
    session_id = uuid4().hex
    db.add(
        RefreshToken(
            user_id=user.id,
            session_id=session_id,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
        )
    )
    return {
        "access_token": create_access_token(user.id, user.role.code, session_id, tenant_id=user.tenant_id),
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": _user_response(user),
    }


def _ensure_tenant_active(user: User) -> None:
    if user.tenant is not None and user.tenant.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "TENANT_INACTIVE", "message": "La empresa asociada al usuario no está activa."},
        )


def register(db: Session, data: RegisterRequest) -> dict[str, object]:
    email = str(data.email).lower()
    if db.scalar(select(User).where(User.email == email, User.tenant_id.is_(None))):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "EMAIL_ALREADY_EXISTS", "message": "El correo electrónico ya está registrado."})
    client_role = db.scalar(select(Role).where(Role.code == "CLIENT", Role.is_active.is_(True)))
    if client_role is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="El rol CLIENT no está configurado")
    user = User(
        role=client_role,
        first_name=data.first_name.strip(),
        last_name=data.last_name.strip(),
        email=email,
        phone=data.phone,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    db.flush()
    db.refresh(user)
    return _issue_tokens(db, user)


def login(db: Session, email: str, password: str) -> dict[str, object]:
    candidates = db.scalars(
        select(User)
        .options(
            joinedload(User.tenant),
            joinedload(User.role).joinedload(Role.permissions),
            selectinload(User.branches),
        )
        .where(User.email == email.lower())
        .order_by(User.id)
    ).unique().all()
    user = next((candidate for candidate in candidates if verify_password(password, candidate.password_hash)), None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "INVALID_CREDENTIALS", "message": "Correo o contraseña incorrectos."})
    if not user.is_active or not user.role.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"code": "USER_INACTIVE", "message": "El usuario está inactivo."})
    _ensure_tenant_active(user)
    return _issue_tokens(db, user)


def refresh(db: Session, raw_token: str) -> dict[str, object]:
    token_record = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(raw_token)))
    now = datetime.now(UTC)
    if token_record is None or token_record.revoked_at is not None or _as_utc(token_record.expires_at) <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "INVALID_REFRESH_TOKEN", "message": "La sesión de renovación no es válida."})
    user = db.scalar(
        select(User)
        .options(
            joinedload(User.tenant),
            joinedload(User.role).joinedload(Role.permissions),
            selectinload(User.branches),
        )
        .where(User.id == token_record.user_id)
    )
    if user is None or not user.is_active or not user.role.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"code": "USER_INACTIVE", "message": "El usuario está inactivo."})
    _ensure_tenant_active(user)
    token_record.revoked_at = now
    return _issue_tokens(db, user)


def logout(db: Session, raw_token: str | None) -> None:
    if not raw_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "REFRESH_TOKEN_REQUIRED", "message": "Se requiere el refresh token para cerrar la sesión."})
    token_record = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(raw_token)))
    if token_record is None or token_record.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "INVALID_REFRESH_TOKEN", "message": "La sesión de renovación no es válida."})
    token_record.revoked_at = datetime.now(UTC)
