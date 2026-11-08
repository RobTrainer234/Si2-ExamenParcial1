from collections.abc import Mapping

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.core.models import Bitacora, User


def record_audit(
    db: Session,
    user: User | None,
    action: str,
    entity_type: str,
    entity_id: int | None,
    description: str,
    *,
    old_values: Mapping[str, object] | None = None,
    new_values: Mapping[str, object] | None = None,
    tenant_id: int | None = None,
) -> Bitacora:
    resolved_tenant_id = (
        tenant_id
        if tenant_id is not None
        else (user.tenant_id if user is not None else db.info.get("tenant_id"))
    )
    entry = Bitacora(
        tenant_id=resolved_tenant_id,
        user_id=user.id if user else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        old_values=jsonable_encoder(dict(old_values)) if old_values else None,
        new_values=jsonable_encoder(dict(new_values)) if new_values else None,
    )
    db.add(entry)
    return entry
