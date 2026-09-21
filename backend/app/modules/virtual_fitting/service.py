from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.models import Product, User, VirtualFittingSession
from app.modules.catalog.service import get_catalog_product
from app.modules.virtual_fitting.schemas import VirtualFittingStartRequest


def error(code: str, message: str, http_status: int = status.HTTP_400_BAD_REQUEST) -> HTTPException:
    return HTTPException(status_code=http_status, detail={"code": code, "message": message})


def _primary_image(product: Product) -> str | None:
    images = sorted(product.images, key=lambda item: item.sort_order)
    primary = next((image for image in images if image.is_primary), None)
    return (primary or images[0]).image_url if images else None


def _query():
    return select(VirtualFittingSession).options(selectinload(VirtualFittingSession.product).selectinload(Product.images))


def serialize(item: VirtualFittingSession) -> dict[str, object]:
    return {"id": item.id, "customer_id": item.customer_id, "product_id": item.product_id, "product_name": item.product.name, "image_url": _primary_image(item.product), "status": item.status, "device_info": item.device_info, "started_at": item.started_at, "ended_at": item.ended_at}


def start_session(db: Session, data: VirtualFittingStartRequest, user: User) -> VirtualFittingSession:
    product = get_catalog_product(db, data.product_id)
    session = VirtualFittingSession(customer_id=user.id, product_id=product.id, status="STARTED", device_info=data.device_info)
    db.add(session)
    db.flush()
    return db.scalar(_query().where(VirtualFittingSession.id == session.id))


def get_session(db: Session, session_id: int) -> VirtualFittingSession:
    item = db.scalar(_query().where(VirtualFittingSession.id == session_id))
    if item is None:
        raise error("VIRTUAL_FITTING_SESSION_NOT_FOUND", "Sesión de vestidor no encontrada.", status.HTTP_404_NOT_FOUND)
    return item


def finish_session(db: Session, session_id: int, user: User) -> VirtualFittingSession:
    item = get_session(db, session_id)
    if item.customer_id != user.id:
        raise error("VIRTUAL_FITTING_FORBIDDEN", "No puedes modificar esta sesión.", status.HTTP_403_FORBIDDEN)
    if item.status == "FINISHED":
        return item
    item.status = "FINISHED"
    item.ended_at = datetime.now(UTC)
    db.flush()
    return get_session(db, item.id)


def list_mine(db: Session, user: User) -> list[VirtualFittingSession]:
    return db.scalars(_query().where(VirtualFittingSession.customer_id == user.id).order_by(VirtualFittingSession.started_at.desc())).all()
