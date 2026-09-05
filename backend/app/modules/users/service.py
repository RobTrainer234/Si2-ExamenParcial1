from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.models import Branch, Role, Supplier, User
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
        "branch_ids": [branch.id for branch in user.branches],
        "supplier_id": user.supplier_id,
    }


def list_users(db: Session, page: int, page_size: int, query: str | None) -> dict[str, object]:
    statement = select(User).options(joinedload(User.role), selectinload(User.branches)).order_by(User.id.desc())
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
    user = db.scalar(select(User).options(joinedload(User.role), selectinload(User.branches)).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "USER_NOT_FOUND", "message": "Usuario no encontrado."})
    return user


def _get_role(db: Session, role_code: str) -> Role:
    role = db.scalar(select(Role).where(Role.code == role_code.upper(), Role.is_active.is_(True)))
    if role is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "ROLE_NOT_FOUND", "message": "El rol indicado no existe o está inactivo."})
    return role


def _set_branches(db: Session, user: User, branch_ids: list[int], role_code: str) -> None:
    unique_ids = set(branch_ids)
    if len(unique_ids) != len(branch_ids):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "BRANCH_DUPLICATE", "message": "No se puede repetir una sucursal."})
    if role_code not in {"BRANCH_MANAGER", "CASHIER"} and unique_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "BRANCH_ROLE_MISMATCH", "message": "Solo los encargados y cajeros pueden tener sucursales asignadas."})
    branches = db.scalars(select(Branch).where(Branch.id.in_(unique_ids), Branch.is_active.is_(True))).all() if unique_ids else []
    if {branch.id for branch in branches} != unique_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "BRANCH_NOT_FOUND_OR_INACTIVE", "message": "Una o más sucursales no existen o están inactivas."})
    user.branches = branches


def _set_supplier(db: Session, user: User, supplier_id: int | None, role_code: str) -> None:
    if supplier_id is None:
        if role_code == "SUPPLIER":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "SUPPLIER_REQUIRED", "message": "Los usuarios con rol SUPPLIER deben asociarse a un proveedor."})
        user.supplier_id = None
        return
    if role_code != "SUPPLIER":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "SUPPLIER_ROLE_MISMATCH", "message": "Solo los usuarios con rol SUPPLIER pueden asociarse a un proveedor."})
    supplier = db.scalar(select(Supplier).where(Supplier.id == supplier_id, Supplier.is_active.is_(True)))
    if supplier is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "SUPPLIER_NOT_FOUND_OR_INACTIVE", "message": "El proveedor no existe o está inactivo."})
    existing = db.scalar(select(User.id).where(User.supplier_id == supplier_id, User.id != user.id))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "SUPPLIER_ALREADY_ASSIGNED", "message": "El proveedor ya tiene un usuario asociado."})
    user.supplier_id = supplier_id


def create_user(db: Session, data: AdminUserCreateRequest) -> User:
    email = str(data.email).lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "EMAIL_ALREADY_EXISTS", "message": "El correo electrónico ya está registrado."})
    role = _get_role(db, data.role)
    user = User(
        role=role,
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
    _set_branches(db, user, data.branch_ids, role.code)
    _set_supplier(db, user, data.supplier_id, role.code)
    db.flush()
    return get_user(db, user.id)


def update_user(db: Session, user: User, data: UserUpdateRequest, admin_id: int) -> User:
    if user.id == admin_id and data.role and data.role.upper() != "ADMIN":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "SELF_ROLE_CHANGE_FORBIDDEN", "message": "No puedes quitarte el rol ADMIN."})
    values = data.model_dump(exclude_unset=True)
    branch_ids = values.pop("branch_ids", None)
    supplier_id = values.pop("supplier_id", None)
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
    if data.role and branch_ids is None:
        branch_ids = [branch.id for branch in user.branches]
    if branch_ids is not None:
        _set_branches(db, user, branch_ids, user.role.code)
    if data.supplier_id is not None or "supplier_id" in data.model_fields_set:
        _set_supplier(db, user, supplier_id, user.role.code)
    elif data.role and user.role.code != "SUPPLIER":
        _set_supplier(db, user, None, user.role.code)
    elif data.role and user.role.code == "SUPPLIER" and user.supplier_id is None:
        _set_supplier(db, user, None, user.role.code)
    db.flush()
    return get_user(db, user.id)


def set_active(db: Session, user: User, active: bool, admin_id: int) -> User:
    if user.id == admin_id and not active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "SELF_DEACTIVATION_FORBIDDEN", "message": "No puedes desactivar tu propio usuario."})
    user.is_active = active
    db.flush()
    return get_user(db, user.id)
