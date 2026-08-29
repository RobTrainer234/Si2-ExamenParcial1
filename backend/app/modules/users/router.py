from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.database import get_db
from app.core.models import User
from app.modules.auth.dependencies import require_admin
from app.modules.users import service
from app.modules.users.schemas import AdminUserCreateRequest, UserPage, UserResponse, UserUpdateRequest

router = APIRouter(prefix="/users", tags=["users"])
AdminUser = Annotated[User, Depends(require_admin)]


@router.get("", response_model=UserPage)
def list_users(
    _: AdminUser,
    db=Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=100),
):
    return service.list_users(db, page, page_size, q)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(data: AdminUserCreateRequest, _: AdminUser, db=Depends(get_db)):
    user = service.create_user(db, data)
    db.commit()
    return service.serialize_user(user)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, _: AdminUser, db=Depends(get_db)):
    return service.serialize_user(service.get_user(db, user_id))


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, data: UserUpdateRequest, admin: AdminUser, db=Depends(get_db)):
    user = service.update_user(db, service.get_user(db, user_id), data, admin.id)
    db.commit()
    return service.serialize_user(user)


@router.patch("/{user_id}/activate", response_model=UserResponse)
def activate_user(user_id: int, admin: AdminUser, db=Depends(get_db)):
    user = service.set_active(db, service.get_user(db, user_id), True, admin.id)
    db.commit()
    return service.serialize_user(user)


@router.patch("/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(user_id: int, admin: AdminUser, db=Depends(get_db)):
    user = service.set_active(db, service.get_user(db, user_id), False, admin.id)
    db.commit()
    return service.serialize_user(user)
