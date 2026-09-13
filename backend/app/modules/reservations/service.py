from datetime import UTC, datetime, timedelta
from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.audit import record_audit
from app.core.models import Branch, Inventory, ProductVariant, Reservation, ReservationItem, User
from app.modules.inventory.service import release_stock, reserve_stock
from app.modules.reservations.schemas import ReservationCreateRequest, ReservationStatusRequest


def error(code: str, message: str, http_status: int) -> HTTPException:
    return HTTPException(status_code=http_status, detail={"code": code, "message": message})


def reservation_query():
    return select(Reservation).options(
        joinedload(Reservation.customer),
        joinedload(Reservation.branch),
        joinedload(Reservation.items).joinedload(ReservationItem.product_variant).joinedload(ProductVariant.product),
        joinedload(Reservation.items).joinedload(ReservationItem.product_variant).joinedload(ProductVariant.size),
        joinedload(Reservation.items).joinedload(ReservationItem.product_variant).joinedload(ProductVariant.color),
    )


def get_reservation(db: Session, reservation_id: int) -> Reservation:
    reservation = db.scalar(reservation_query().where(Reservation.id == reservation_id))
    if reservation is None:
        raise error("RESERVATION_NOT_FOUND", "Reserva no encontrada.", status.HTTP_404_NOT_FOUND)
    return reservation


def serialize_reservation(reservation: Reservation) -> dict[str, object]:
    return {
        "id": reservation.id,
        "customer_id": reservation.customer_id,
        "customer_name": f"{reservation.customer.first_name} {reservation.customer.last_name}",
        "branch_id": reservation.branch_id,
        "branch_name": reservation.branch.name,
        "scheduled_for": reservation.scheduled_for,
        "status": reservation.status,
        "notes": reservation.notes,
        "expires_at": reservation.expires_at,
        "created_at": reservation.created_at,
        "items": [
            {
                "id": item.id,
                "product_variant_id": item.product_variant_id,
                "product_id": item.product_variant.product_id,
                "product_name": item.product_variant.product.name,
                "sku": item.product_variant.sku,
                "size_name": item.product_variant.size.name,
                "color_name": item.product_variant.color.name,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
            }
            for item in reservation.items
        ],
    }


def _validate_branch(db: Session, branch_id: int) -> Branch:
    branch = db.scalar(select(Branch).where(Branch.id == branch_id, Branch.is_active.is_(True)))
    if branch is None:
        raise error("BRANCH_NOT_FOUND_OR_INACTIVE", "La sucursal no existe o está inactiva.", status.HTTP_400_BAD_REQUEST)
    return branch


def _validate_schedule(scheduled_for: datetime | None) -> None:
    if scheduled_for is not None:
        value = scheduled_for if scheduled_for.tzinfo else scheduled_for.replace(tzinfo=UTC)
        if value <= datetime.now(UTC):
            raise error("INVALID_SCHEDULE", "La fecha de visita debe ser futura.", status.HTTP_400_BAD_REQUEST)


def create_reservation(db: Session, data: ReservationCreateRequest, customer: User) -> Reservation:
    _validate_branch(db, data.branch_id)
    _validate_schedule(data.scheduled_for)
    reservation = Reservation(
        customer_id=customer.id,
        branch_id=data.branch_id,
        scheduled_for=data.scheduled_for,
        notes=data.notes.strip() if data.notes else None,
        expires_at=(data.scheduled_for + timedelta(hours=2)) if data.scheduled_for else None,
    )
    db.add(reservation)
    db.flush()
    for request_item in data.items:
        variant = db.scalar(select(ProductVariant).options(joinedload(ProductVariant.product)).where(ProductVariant.id == request_item.product_variant_id, ProductVariant.is_active.is_(True)))
        if variant is None or not variant.product.is_active:
            raise error("VARIANT_NOT_FOUND_OR_INACTIVE", "Una variante no existe o está inactiva.", status.HTTP_400_BAD_REQUEST)
        inventory = db.scalar(select(Inventory.id).where(Inventory.branch_id == data.branch_id, Inventory.product_variant_id == request_item.product_variant_id))
        if inventory is None:
            raise error("INVENTORY_NOT_FOUND", "No existe inventario para una variante en la sucursal seleccionada.", status.HTTP_409_CONFLICT)
        item = ReservationItem(reservation_id=reservation.id, product_variant_id=request_item.product_variant_id, quantity=request_item.quantity, unit_price=variant.product.price)
        db.add(item)
        db.flush()
        reserve_stock(db, inventory, request_item.quantity, reservation.id)
    record_audit(db, customer, "CREATE", "reservation", reservation.id, "Reserva de prendas creada.", new_values={"branch_id": reservation.branch_id, "status": reservation.status})
    return get_reservation(db, reservation.id)


def list_reservations(db: Session, page: int, page_size: int, *, customer_id: int | None = None, branch_id: int | None = None, reservation_status: str | None = None) -> dict[str, object]:
    statement = reservation_query().order_by(Reservation.created_at.desc())
    count_statement = select(func.count(Reservation.id))
    filters = []
    if customer_id is not None:
        filters.append(Reservation.customer_id == customer_id)
    if branch_id is not None:
        filters.append(Reservation.branch_id == branch_id)
    if reservation_status is not None:
        filters.append(Reservation.status == reservation_status)
    if filters:
        statement = statement.where(*filters)
        count_statement = count_statement.where(*filters)
    total = db.scalar(count_statement) or 0
    reservations = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).unique().all()
    return {"items": [serialize_reservation(item) for item in reservations], "page": page, "page_size": page_size, "total": total, "total_pages": ceil(total / page_size) if total else 0}


ALLOWED_TRANSITIONS = {
    "PENDING": {"PREPARING", "CANCELLED", "EXPIRED"},
    "PREPARING": {"READY", "CANCELLED", "EXPIRED"},
    "READY": {"ATTENDED", "CANCELLED", "EXPIRED"},
    "ATTENDED": set(),
    "CANCELLED": set(),
    "EXPIRED": set(),
}


def change_status(db: Session, reservation: Reservation, data: ReservationStatusRequest, user: User) -> Reservation:
    if data.status not in ALLOWED_TRANSITIONS.get(reservation.status, set()):
        raise error("INVALID_RESERVATION_TRANSITION", f"No se puede cambiar de {reservation.status} a {data.status}.", status.HTTP_409_CONFLICT)
    old_status = reservation.status
    reservation.status = data.status
    if data.notes is not None:
        reservation.notes = data.notes.strip() or None
    if data.status in {"CANCELLED", "EXPIRED"}:
        for item in reservation.items:
            inventory_id = db.scalar(select(Inventory.id).where(Inventory.branch_id == reservation.branch_id, Inventory.product_variant_id == item.product_variant_id))
            if inventory_id is not None:
                release_stock(db, inventory_id, item.quantity, reservation.id)
    record_audit(db, user, "UPDATE", "reservation", reservation.id, "Estado de reserva actualizado.", old_values={"status": old_status}, new_values={"status": reservation.status})
    db.flush()
    return get_reservation(db, reservation.id)
