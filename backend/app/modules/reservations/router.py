from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from math import ceil
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.core.models import Branch, User
from app.modules.auth.dependencies import require_branch_access, require_permission
from app.modules.reservations import service
from app.modules.reservations.expiration import expire_due_reservations
from app.modules.reservations.schemas import ReservationCreateRequest, ReservationPage, ReservationResponse, ReservationStatusRequest
from app.modules.locations.service import serialize_branch


router = APIRouter(prefix="/reservations", tags=["reservations"])
ClientReservationUser = Annotated[User, Depends(require_permission("reservations.read"))]
ReservationCreator = Annotated[User, Depends(require_permission("reservations.create"))]
ReservationCanceller = Annotated[User, Depends(require_permission("reservations.cancel"))]
BranchReservationUser = Annotated[User, Depends(require_permission("reservations.manage"))]


@router.get("/branches")
def list_reservation_branches(current_user: BranchReservationUser, db=Depends(get_db)):
    statement = select(Branch).options(joinedload(Branch.city)).order_by(Branch.name)
    count_statement = select(func.count(Branch.id))
    if current_user.role.code != "ADMIN":
        allowed = {branch.id for branch in current_user.branches}
        statement = statement.where(Branch.id.in_(allowed))
        count_statement = count_statement.where(Branch.id.in_(allowed))
    branches = db.scalars(statement).all()
    total = db.scalar(count_statement) or 0
    return {"items": [serialize_branch(branch) for branch in branches], "page": 1, "page_size": max(total, 1), "total": total, "total_pages": ceil(total / max(total, 1)) if total else 0}


@router.post("", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def create_reservation(data: ReservationCreateRequest, current_user: ReservationCreator, db=Depends(get_db)):
    try:
        expire_due_reservations(db)
        reservation = service.create_reservation(db, data, current_user)
    except Exception:
        db.rollback()
        raise
    db.commit()
    return service.serialize_reservation(reservation)


@router.get("/mine", response_model=ReservationPage)
def list_my_reservations(current_user: ClientReservationUser, db=Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), reservation_status: str | None = Query(None, alias="status", max_length=30)):
    expire_due_reservations(db)
    db.commit()
    return service.list_reservations(db, page, page_size, customer_id=current_user.id, reservation_status=reservation_status)


@router.get("/branch", response_model=ReservationPage)
def list_branch_reservations(current_user: BranchReservationUser, db=Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), branch_id: int = Query(..., gt=0), reservation_status: str | None = Query(None, alias="status", max_length=30)):
    require_branch_access(current_user, branch_id)
    expire_due_reservations(db)
    db.commit()
    return service.list_reservations(db, page, page_size, branch_id=branch_id, reservation_status=reservation_status)


@router.get("/{reservation_id}", response_model=ReservationResponse)
def get_reservation(reservation_id: int, current_user: User = Depends(require_permission("reservations.read")), db=Depends(get_db)):
    expire_due_reservations(db)
    db.commit()
    reservation = service.get_reservation(db, reservation_id)
    if current_user.role.code != "ADMIN" and reservation.customer_id != current_user.id:
        require_branch_access(current_user, reservation.branch_id)
    return service.serialize_reservation(reservation)


@router.patch("/{reservation_id}/cancel", response_model=ReservationResponse)
def cancel_reservation(reservation_id: int, current_user: ReservationCanceller, db=Depends(get_db)):
    expire_due_reservations(db)
    reservation = service.get_reservation(db, reservation_id)
    if current_user.role.code != "ADMIN" and reservation.customer_id != current_user.id:
        raise service.error("RESERVATION_FORBIDDEN", "No puedes cancelar esta reserva.", status.HTTP_403_FORBIDDEN)
    result = service.change_status(db, reservation, ReservationStatusRequest(status="CANCELLED"), current_user)
    db.commit()
    return service.serialize_reservation(result)


@router.patch("/{reservation_id}/status", response_model=ReservationResponse)
def update_reservation_status(reservation_id: int, data: ReservationStatusRequest, current_user: BranchReservationUser, db=Depends(get_db)):
    expire_due_reservations(db)
    reservation = service.get_reservation(db, reservation_id)
    require_branch_access(current_user, reservation.branch_id)
    result = service.change_status(db, reservation, data, current_user)
    db.commit()
    return service.serialize_reservation(result)
