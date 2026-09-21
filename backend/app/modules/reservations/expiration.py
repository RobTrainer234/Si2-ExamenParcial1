from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.models import Reservation
from app.modules.reservations import service
from app.modules.reservations.schemas import ReservationStatusRequest


def expire_due_reservations(db: Session, now: datetime | None = None) -> int:
    current_time = now or datetime.now(UTC)
    reservation_ids = db.scalars(
        select(Reservation.id).where(
            Reservation.status.in_(("PENDING", "PREPARING", "READY")),
            Reservation.expires_at.is_not(None),
            Reservation.expires_at <= current_time,
        )
    ).all()
    expired = 0
    for reservation_id in reservation_ids:
        reservation = service.get_locked_reservation(db, reservation_id)
        expires_at = reservation.expires_at
        if expires_at is not None and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if reservation.status not in {"PENDING", "PREPARING", "READY"} or expires_at is None or expires_at > current_time:
            continue
        service.change_status(db, reservation, ReservationStatusRequest(status="EXPIRED"), None)
        expired += 1
    return expired


if __name__ == "__main__":
    from app.core.database import SessionLocal

    with SessionLocal.begin() as db:
        print(f"Expired reservations: {expire_due_reservations(db)}")
