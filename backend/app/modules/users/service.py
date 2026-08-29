from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.models import Role, User
from app.core.security import hash_password
from app.modules.users.schemas import AdminUserCreateRequest, UserUpdateRequest


def serialize_user(user: User) -> dict[str, object]:
    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role.code,
        "is_active": user.is_active,
    }


def list_users(db: Session, page: int, page_size: int, query: str | None) -> dict[str, object]:
    statement = select(User).options(joinedload(User.role)).order_by(User.id.desc())
    count_statement = select(func.count(User.id))
    if query:
        search = f"%{query.strip()}%"
        condition = or_(User.first_name.ilike(search), User.last_name.ilike(search), User.email.ilike(search))
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    total = db.scalar(count_statement) or 0
    users = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
    return {
        "items": [serialize_user(user) for user in users],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": ceil(total / page_size) if total else 0,
    }


def get_user(db: Session, user_id: int) -> User:
    user = db.scalar(select(User).options(joinedload(User.role)).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "USER_NOT_FOUND", "message": "Usuario no encontrado."})
    return user


def _get_role(db: Session, role_code: str) -> Role:
    role = db.scalar(select(Role).where(Role.code == role_code.upper(), Role.is_active.is_(True)))
    if role is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "ROLE_NOT_FOUND", "message": "El rol indicado no existe o está inactivo."})
    return role


def create_user(db: Session, data: AdminUserCreateRequest) -> User:
    email = str(data.email).lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "EMAIL_ALREADY_EXISTS", "message": "El correo electrónico ya está registrado."})
    user = User(
        role=_get_role(db, data.role),
        first_name=data.first_name.strip(),
        last_name=data.last_name.strip(),
        email=email,
        phone=data.phone,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "USER_CONFLICT", "message": "No se pudo crear el usuario."}) from exc
    db.refresh(user)
    return get_user(db, user.id)


def update_user(db: Session, user: User, data: UserUpdateRequest, admin_id: int) -> User:
    if user.id == admin_id and data.role and data.role.upper() != "ADMIN":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "SELF_ROLE_CHANGE_FORBIDDEN", "message": "No puedes quitarte el rol ADMIN."})
    if data.email:
        email = str(data.email).lower()
        existing = db.scalar(select(User.id).where(User.email == email, User.id != user.id))
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "EMAIL_ALREADY_EXISTS", "message": "El correo electrónico ya está registrado."})
        user.email = email
    if data.first_name is not None:
        user.first_name = data.first_name.strip()
    if data.last_name is not None:
        user.last_name = data.last_name.strip()
    if data.phone is not None:
        user.phone = data.phone
    if data.role:
        user.role = _get_role(db, data.role)
    db.flush()
    return get_user(db, user.id)


def set_active(db: Session, user: User, active: bool, admin_id: int) -> User:
    if user.id == admin_id and not active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "SELF_DEACTIVATION_FORBIDDEN", "message": "No puedes desactivar tu propio usuario."})
    user.is_active = active
    db.flush()
    return get_user(db, user.id)
