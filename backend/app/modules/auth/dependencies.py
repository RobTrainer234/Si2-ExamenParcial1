from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.database import get_db
from app.core.models import RefreshToken, Role, User
from app.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DbSession) -> User:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado", headers={"WWW-Authenticate": "Bearer"})
    try:
        user_id = int(str(payload["sub"]))
        session_id = str(payload["jti"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido", headers={"WWW-Authenticate": "Bearer"}) from exc
    session = db.scalar(select(RefreshToken).where(RefreshToken.session_id == session_id, RefreshToken.revoked_at.is_(None), RefreshToken.expires_at > datetime.now(UTC)))
    user = db.scalar(select(User).options(joinedload(User.role).joinedload(Role.permissions), selectinload(User.branches)).where(User.id == user_id))
    if session is None or session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión inválida o cerrada", headers={"WWW-Authenticate": "Bearer"})
    if user is None or not user.is_active or not user.role.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no disponible", headers={"WWW-Authenticate": "Bearer"})
    return user


def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if current_user.role.code != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ADMIN_ROLE_REQUIRED", "message": "Se requiere el rol ADMIN."},
        )
    return current_user


def require_permission(permission_code: str):
    def dependency(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role.code == "ADMIN" or any(permission.code == permission_code and permission.is_active for permission in current_user.role.permissions):
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_REQUIRED", "message": "No tienes permisos para realizar esta operación."},
        )

    return dependency


def require_branch_access(current_user: Annotated[User, Depends(get_current_user)], branch_id: int) -> User:
    if current_user.role.code != "ADMIN" and branch_id not in {branch.id for branch in current_user.branches}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "BRANCH_ACCESS_REQUIRED", "message": "No tienes acceso a esta sucursal."},
        )
    return current_user
