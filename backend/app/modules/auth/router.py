from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.core.database import get_db
from app.core.models import User
from app.modules.auth import service
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import AuthResponse, LoginRequest, LogoutRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db=Depends(get_db)):
    result = service.register(db, data)
    db.commit()
    return result


@router.post("/login", response_model=AuthResponse)
def login(data: LoginRequest, db=Depends(get_db)):
    result = service.login(db, str(data.email), data.password)
    db.commit()
    return result


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest, db=Depends(get_db)):
    result = service.refresh(db, data.refresh_token)
    db.commit()
    return result


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(data: LogoutRequest, db=Depends(get_db)) -> Response:
    service.logout(db, data.refresh_token)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserResponse)
def me(current_user: Annotated[User, Depends(get_current_user)]) -> dict[str, object]:
    return {
        "id": current_user.id,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "role": current_user.role.code,
        "is_active": current_user.is_active,
        "permissions": sorted(permission.code for permission in current_user.role.permissions if permission.is_active),
        "supplier_id": current_user.supplier_id,
    }
