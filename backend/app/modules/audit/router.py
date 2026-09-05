from math import ceil
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.models import Bitacora, User
from app.modules.auth.dependencies import require_admin
from app.modules.audit.schemas import AuditPage

router = APIRouter(prefix="/audit", tags=["audit"])
AdminUser = Annotated[User, Depends(require_admin)]


@router.get("", response_model=AuditPage)
def list_audit(
    _: AdminUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: str | None = Query(None, max_length=30),
    entity_type: str | None = Query(None, max_length=100),
):
    conditions = []
    if action:
        conditions.append(Bitacora.action == action.upper())
    if entity_type:
        conditions.append(Bitacora.entity_type == entity_type)
    count_statement = select(func.count(Bitacora.id)).where(*conditions)
    statement = select(Bitacora).options(joinedload(Bitacora.user)).where(*conditions).order_by(Bitacora.id.desc())
    total = db.scalar(count_statement) or 0
    entries = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
    return {
        "items": [{
            "id": entry.id,
            "user_id": entry.user_id,
            "user_name": f"{entry.user.first_name} {entry.user.last_name}" if entry.user else None,
            "action": entry.action,
            "entity_type": entry.entity_type,
            "entity_id": entry.entity_id,
            "description": entry.description,
            "old_values": entry.old_values,
            "new_values": entry.new_values,
            "created_at": entry.created_at,
        } for entry in entries],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": ceil(total / page_size) if total else 0,
    }
